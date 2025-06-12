from pydantic import BaseModel, model_validator
from common.utils.common_utils import create_uuid
from common.utils.file_util import open_and_base64
from typing import Optional, List, Dict, Any, Tuple
from common.utils.playwright import PlaywrightBrowser
from common.utils.playwright.types import InteractiveRegion
from common.utils.playwright.playwright_controller import PlaywrightController
from common.utils.playwright.utils.set_of_mark import add_set_of_mark
from application.domain.generators.tools import Tool
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk
from common.utils.playwright.url_status_manager import (
    UrlStatusManager,
    UrlStatus,
    URL_ALLOWED,
    URL_REJECTED,
)
from playwright.async_api import (
    BrowserContext,
    Download,
    Page,
)
import tldextract
import time
import os
import re
import json
import PIL.Image
import io
from datetime import datetime

from common.core.logger import get_logger

logger = get_logger(__name__)

class AgentState(BaseModel):
    did_lazy_init: bool = False

    def lazy_init(self):
        self.did_lazy_init = True

class Agent(BaseModel):

    id: str
    name: str
    tools_group_list: List[Dict[str, Any]]
    description: str
    agent_prompts: Dict[str, str]

    @model_validator(mode='after')
    def check_dict_keys(cls, values):
        """
        验证tools_group_list的key格式
        :param values:
        :return:
        """
        tools_group_list = values.tools_group_list
        for tools_group in tools_group_list:
            for key in tools_group.keys():
                if key not in ["group_name", "type"]:
                    raise ValueError(f"Invalid key '{key}', only 'group_name' and 'type' are allowed.")
            return values

    def make_instance(self) -> "AgentInstance":
        instance = AgentInstance()
        instance.instance_id = create_uuid()
        instance.agent = self
        return instance
        # return AgentInstance(
        #     # id=self.id,
        #     # name=self.name,
        #     # tools_group_list=self.tools_group_list,
        #     # description=self.description,
        #     # agent_prompts=self.agent_prompts,
        #     agent=self,
        #     instance_id=create_uuid(),
        # )

    # def model_dump(self, **kwargs):
        #     # 使用 super() 获取字典格式
        #     data = super().model_dump()
        #
        #     # 用于存储已经遇到的 (group_name, type) 或 (mcp_server_name, type) 组合
        #     seen_combinations = set()
        #
        #     # 筛选出不重复的工具
        #     filtered_tools = []
        #
        #     # 持久化只保存tools组的名字和类型
        #     if 'tools' in data:
        #         # dict_tools: List[Dict[str, Any]] = []
        #         for tool in data['tools']:
        #             combination = None
        #             if tool['group_name']:
        #                 combination = (tool['group_name'], tool['type'])
        #             elif tool['mcp_server_name']:
        #                 combination = (tool['mcp_server_name'], tool['type'])
        #             # 如果该组合未被遇到过，则添加到结果列表中
        #             if combination and combination not in seen_combinations:
        #                 filtered_tools.append({
        #                     "group_name": tool['group_name'] if tool['group_name'] else tool['mcp_server_name'],
        #                     "type": tool['type'].value
        #                 })
        #                 seen_combinations.add(combination)
        #         data['tools'] = filtered_tools
        #
        #     return data

        # @classmethod
        # def from_init(cls, name: str, tools: List[Tool], description: str) -> "Agent":
        #     return cls(id=create_uuid(), tools=tools, name=name, description=description)
class AgentInstance:

    def __init__(self):

        # 通用属性
        self.agent: Agent
        self.instance_id: str
        self.system_prompt: Optional[str] =None
        # self.prompts: Dict[str, str] = {}
        self.status: AgentState = AgentState()
        self.config: Optional[Dict[str, Any]] = None

        self.tools: Optional[List[Tool]] = None
        self.default_tools_name_list: Optional[List[str]] = []
        self.use_tools_name_list: Optional[List[str]] = []

        self._last_outside_message: Optional[str] = None

        # 浏览器
        # Size of the image we send to the MLM
        # Current values represent a 0.85 scaling to fit within the GPT-4v short-edge constraints (768px)
        self.MLM_HEIGHT = 765
        self.MLM_WIDTH = 1224

        self.debug_dir: str = "debug_dir"
        self.browser_screenshot_dir: str = "browser_screenshot"
        self.browser: Optional[PlaywrightBrowser] = None
        # self.start_page: str = "about:blank"
        self.start_page: str = "https://www.baidu.com"
        self.animate_actions: bool = False
        self.to_save_screenshots: bool = True
        self.to_resize_viewport: bool = True
        self.url_statuses: Dict[str, UrlStatus] | None = None
        self.url_block_list: List[str] | None = None
        self.single_tab_mode: bool = False
        self.viewport_height: int = 1440
        self.viewport_width: int = 1440
        self.downloads_folder: str = "downloads"
        # runtime
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._url_status_manager: UrlStatusManager = UrlStatusManager(
            url_statuses=self.url_statuses, url_block_list=self.url_block_list
        )
        self._last_rejected_url: Optional[str] = None

        # Define the download handler
        def _download_handler(download: Download) -> None:
            _last_download = download

        self._download_handler = _download_handler

        self._playwright_controller = PlaywrightController(
            animate_actions=self.animate_actions,
            downloads_folder=self.downloads_folder,
            viewport_width=self.viewport_width,
            viewport_height=self.viewport_height,
            _download_handler=self._download_handler,
            to_resize_viewport=self.to_resize_viewport,
            single_tab_mode=self.single_tab_mode,
            url_status_manager=self._url_status_manager,
            url_validation_callback=self._check_url_and_generate_msg,
        )

    def setting(self, config: Optional[Dict[str, Any]] = None):
        self.config = config

    async def get_tabs_info(self) -> Tuple[int, str]:
        """Returns the number of tabs and a newline delineated string describing each of them. An example of the string is:

        Tab 0: <Tab_Title> (<URL>) [CURRENTLY SHOWN] [CONTROLLED]
        Tab 1: <Tab_Title> (<URL>)
        Tab 2: <Tab_Title> (<URL>)

        Returns:
            Tuple containing:
            - int: The number of tabs
            - str: String describing each tab.
        """
        num_tabs = 1
        assert self._context is not None
        assert self._page is not None
        tabs_information = await self._playwright_controller.get_tabs_information(
            self._context,
            self._page,  # Pass the current page
        )
        num_tabs = len(tabs_information)
        tabs_information_str = "\n".join(
            [
                f"Tab {tab['index']}: {tab['title']} ({tab['url']})"
                f"{' [CURRENTLY SHOWN]' if tab['is_active'] else ''}"
                f"{' [CONTROLLED]' if tab['is_controlled'] else ''}"
                for tab in tabs_information
            ]
        )
        return num_tabs, tabs_information_str

    async def _check_url_and_generate_msg(self, url: str) -> Tuple[str, bool]:
        """Returns a message to caller if the URL is not allowed and a boolean indicating if the user has approved the URL."""
        # TODO: Hacky check to see if the URL was aborted. Find a better way to do this
        if url == "chrome-error://chromewebdata/":
            if self._last_rejected_url is not None:
                last_rejected_url = self._last_rejected_url
                self._last_rejected_url = None
                return (
                    f"I am not allowed to access the website {last_rejected_url} because it is not in the list of websites I can access and the user has declined to approve it.",
                    False,
                )

        if self._url_status_manager.is_url_blocked(url):
            return (
                f"I am not allowed to access the website {url} because has been blocked.",
                False,
            )

        if not self._url_status_manager.is_url_allowed(url):
            if not self._url_status_manager.is_url_rejected(url):
                # tldextract will only recombine entries with valid, registered hostnames. We'll just use the straight url for anything else.
                domain = tldextract.extract(url).fqdn
                if not domain:
                    domain = url
                response = False
                self._url_status_manager.set_url_status(domain, URL_REJECTED)

            self._last_rejected_url = url
            return (
                f"I am not allowed to access the website {url} because it is not in the list of websites I can access and the user has declined to allow it.",
                False,
            )
        return "", True

    def load_prompt(self, prompt_key: str, **kwargs) -> str:
        return self.agent_prompts[prompt_key]

    def get_status(self) -> AgentState:
        return self.status



    def run(self) -> Dict[str, Any]:
        pass

    async def lazy_init(self) -> None:
        if self.get_status().did_lazy_init:
            return
        await self.browser.__aenter__()
        self._context = self.browser.browser_context
        # Create the page
        assert self._context is not None
        self._context.set_default_timeout(20000)  # 20 sec
        self._page = None
        self._page = await self._context.new_page() # 打开新页面
        await self._playwright_controller.on_new_page(self._page) # 配置当前页面的控制器

        # 设置初始页面
        async def handle_new_page(new_pg: Page) -> None:
            # last resort on new tabs
            assert new_pg is not None
            assert self._page is not None
            await new_pg.wait_for_load_state("domcontentloaded")
            new_url = new_pg.url
            await new_pg.close()
            await self._playwright_controller.visit_page(self._page, new_url)

        if self.single_tab_mode: # 单tab模式确保关闭所有选项卡并指向
            # this will make sure any new tabs will be closed and redirected to the main page
            # it is a last resort, the playwright controller handles most cases
            self._context.on("page", lambda new_pg: handle_new_page(new_pg))

        try:
            await self._playwright_controller.visit_page(self._page, self.start_page)
        except Exception:
            pass

        date_today = datetime.now().strftime("%Y-%m-%d")

        self.system_prompt = self.agent.agent_prompts['WEB_SURFER_SYSTEM_MESSAGE'].format(
            date_today=date_today,
        ).strip()

        # 设置默认工具了列表
        self.default_tools_name_list = [
            "TOOL_STOP_ACTION",
            "TOOL_VISIT_URL",
            "TOOL_WEB_SEARCH",
            "TOOL_CLICK",
            "TOOL_TYPE",
            "TOOL_READ_PAGE_AND_ANSWER",
            "TOOL_SLEEP",
            "TOOL_HOVER",
            "TOOL_HISTORY_BACK",
            "TOOL_KEYPRESS",
            "TOOL_REFRESH_PAGE",
            # TOOL_CLICK_FULL,
        ]

        self.get_status().lazy_init() # 设置初始化完成标识


    async def check_page_accessible(self):
        try:
            assert self._page is not None
            assert (
                await self._playwright_controller.get_interactive_rects(self._page)
                is not None
            )
        except Exception as e:
            # open a new tab and point it to about:blank
            logger.error(f"Page is not accessible, creating a new one: {e}")
            assert self._context is not None
            self._page = await self._playwright_controller.create_new_tab(
                self._context, "about:blank"
            )

    def _target_name(
        self, target: str, rects: Dict[str, InteractiveRegion]
    ) -> str | None:
        """Get the accessible name of a target element.

        Args:
            target (str): ID of the target element
            rects (Dict[str, InteractiveRegion]): Dictionary of interactive page elements

        Returns:
            str | None: The aria name of the element if available, None otherwise
        """
        try:
            return rects[target]["aria_name"].strip()
        except KeyError:
            return None

    def _format_target_list(
            self, ids: List[str], rects: Dict[str, InteractiveRegion]
    ) -> List[str]:
        """
        Format the list of targets in the webpage as a string to be used in the agent's prompt.
        """
        targets: List[str] = []
        for r in list(set(ids)):
            if r in rects:
                # Get the role
                aria_role = rects[r].get("role", "").strip()
                if len(aria_role) == 0:
                    aria_role = rects[r].get("tag_name", "").strip()

                # Get the name
                aria_name = re.sub(
                    r"[\n\r]+", " ", rects[r].get("aria_name", "")
                ).strip()

                # What are the actions?
                actions = ['"click", "hover"']
                if (
                        rects[r]["role"] in ["textbox", "searchbox", "combobox"]
                        or rects[r].get("tag_name") in ["input", "textarea", "search"]
                        or rects[r].get("contenteditable") == "true"
                ):
                    actions.append('"input_text"')
                # if the role is option, add "select" to the actions
                if rects[r]["role"] == "option":
                    actions = ['"select_option"']
                # check if the role is file input
                if aria_role == "input, type=file":
                    actions = ['"upload_file"']
                actions_str = "[" + ",".join(actions) + "]"
                # limit  name to maximum 100 characters
                aria_name = aria_name[:100]
                targets.append(
                    f'{{"id": {r}, "name": "{aria_name}", "role": "{aria_role}", "tools": {actions_str} }}'
                )
        sorted_targets = sorted(
            targets, key=lambda x: int(x.split(",")[0].split(":")[1])
        )

        return sorted_targets

    async def load_pagr_info(self) -> ChatStreamingChunk:
        # Ask the page for interactive elements, then prepare the state-of-mark screenshot
        rects = await self._playwright_controller.get_interactive_rects(self._page)
        viewport = await self._playwright_controller.get_visual_viewport(self._page)
        screenshot = await self._playwright_controller.get_screenshot(self._page)
        som_screenshot, visible_rects, rects_above, rects_below, element_id_mapping = (
            add_set_of_mark(screenshot, rects, use_sequential_ids=True)
        )
        # element_id_mapping is a mapping of new ids to original ids in the page
        # we need to reverse it to get the original ids from the new ids
        # for each element we click, we need to use the original id
        reverse_element_id_mapping = {v: k for k, v in element_id_mapping.items()}
        rects = {reverse_element_id_mapping.get(k, k): v for k, v in rects.items()}

        if self.to_save_screenshots and self.debug_dir is not None:
            current_timestamp = "_" + int(time.time()).__str__()
            screenshot_png_name = "screenshot_som" + current_timestamp + ".png"
            som_screenshot.save(os.path.join(self.debug_dir, screenshot_png_name))
            logger.info(f"Screenshot saved to {self.debug_dir}/{screenshot_png_name}")

        # Get the tabs information
        tabs_information_str = ""
        num_tabs = 1
        if not self.single_tab_mode and self._context is not None:
            num_tabs, tabs_information_str = await self.get_tabs_info()
            tabs_information_str = f"There are {num_tabs} tabs open. The tabs are as follows:\n{tabs_information_str}"

        # 动态设置工具
        # What tools are available?
        self.use_tools_name_list = self.default_tools_name_list.copy()

        # If not in single tab mode, always allow creating new tabs
        if not self.single_tab_mode:
            if "TOOL_CREATE_TAB" not in self.use_tools_name_list:
                self.use_tools_name_list.append("TOOL_CREATE_TAB")

        # If there are multiple tabs, we can switch between them and close them
        if not self.single_tab_mode and num_tabs > 1:
            self.use_tools_name_list.append("TOOL_SWITCH_TAB")
            self.use_tools_name_list.append("TOOL_CLOSE_TAB")

        # We can scroll up
        if viewport["pageTop"] > 5:
            self.use_tools_name_list.append("TOOL_PAGE_UP")

        # Can scroll down
        if (viewport["pageTop"] + viewport["height"] + 5) < viewport["scrollHeight"]:
            self.use_tools_name_list.append("TOOL_PAGE_DOWN")

        # Add select_option tool only if there are option elements
        if any(rect.get("role") == "option" for rect in rects.values()):
            self.use_tools_name_list.append("TOOL_SELECT_OPTION")

        # Focus hint
        focused = await self._playwright_controller.get_focused_rect_id(self._page)
        focused = reverse_element_id_mapping.get(focused, focused)

        focused_hint = ""
        if focused:
            name = self._target_name(focused, rects)
            if name:
                name = f"(and name '{name}') "

            role = "control"
            try:
                role = rects[focused]["role"]
            except KeyError:
                pass

            focused_hint = f"\nThe {role} with ID {focused} {name}currently has the input focus.\n\n"

        # Everything visible
        visible_targets = (
                "\n".join(self._format_target_list(visible_rects, rects)) + "\n\n"
        )

        # Everything else
        other_targets: List[str] = []
        other_targets.extend(self._format_target_list(rects_above, rects))
        other_targets.extend(self._format_target_list(rects_below, rects))


        if len(other_targets) > 0:
            # Extract just the names from the JSON strings
            other_target_names: List[str] = []
            for target in other_targets:
                try:
                    target_dict = json.loads(target)
                    name = target_dict.get("name", "")
                    role = target_dict.get("role", "")
                    other_target_names.append(name if name else f"{role} control")
                except json.JSONDecodeError:
                    continue

            other_targets_str = (
                "Some additional valid interaction targets (not shown, you need to scroll to interact with them) include:\n"
                + ", ".join(other_target_names[:30])
                + "\n\n"
            )
        else:
            other_targets_str = ""

        webpage_text = await self._playwright_controller.get_visible_text(self._page)

        text_prompt = self.agent.agent_prompts['WEB_SURFER_TOOL_PROMPT'].format(
            tabs_information=tabs_information_str,
            last_outside_message=self._last_outside_message,
            webpage_text=webpage_text,
            url=self._page.url,
            visible_targets=visible_targets,
            consider_screenshot="Consider the following screenshot of a web browser,",
            # if self.is_multimodal
            # else "Consider the following webpage",
            other_targets_str=other_targets_str,
            focused_hint=focused_hint,
            # tool_names=tool_names,
        ).strip()

        scaled_som_screenshot = som_screenshot.resize(
            (self.MLM_WIDTH, self.MLM_HEIGHT)
        )
        screenshot_file = PIL.Image.open(io.BytesIO(screenshot))
        scaled_screenshot = screenshot_file.resize(
            (self.MLM_WIDTH, self.MLM_HEIGHT)
        )

        current_timestamp = "_" + int(time.time()).__str__()
        screenshot_som_png_name = "screenshot_som" + current_timestamp + ".png"
        screenshot_som_png_url = os.path.join(self.browser_screenshot_dir, screenshot_som_png_name)
        scaled_som_screenshot.save(screenshot_som_png_url)
        screenshot_png_name = "screenshot" + current_timestamp + ".png"
        screenshot_png_url = os.path.join(self.browser_screenshot_dir, screenshot_png_name)
        scaled_screenshot.save(screenshot_png_url)

        som_screenshot.close()
        screenshot_file.close()
        scaled_screenshot.close()

        screenshot_png_base64_image = open_and_base64(screenshot_png_url)
        screenshot_som_png_base64_image = open_and_base64(screenshot_som_png_url)

        messages = [
            {
                "text": text_prompt,
                "type": "text"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{screenshot_png_base64_image}"
                }
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{screenshot_som_png_base64_image}"
                }
            }
        ]

        chunk = ChatStreamingChunk.from_user(message=messages)
        return chunk