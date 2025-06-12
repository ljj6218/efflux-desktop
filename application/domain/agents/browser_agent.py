from typing import List, Dict, Any, Tuple, Optional, cast
from urllib.parse import quote_plus

from playwright.async_api import Download, BrowserContext, Page

from application.domain.events.event import Event, EventType, EventSubType, EventSource
from application.domain.generators.tools import ToolType, ToolInstance
from application.port.outbound.event_port import EventPort
from application.port.outbound.tools_port import ToolsPort
from common.utils.common_utils import create_uuid
from common.utils.file_util import open_and_base64
from common.utils.playwright import PlaywrightController, PlaywrightBrowser, InteractiveRegion, LocalPlaywrightBrowser
from common.utils.playwright.url_status_manager import UrlStatusManager, UrlStatus, URL_REJECTED
from common.utils.playwright.utils.set_of_mark import add_set_of_mark

from application.domain.agents.agent import AgentInstance
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk
from application.domain.generators.generator import LLMGenerator
from application.port.outbound.conversation_port import ConversationPort
from application.port.outbound.generators_port import GeneratorsPort
from application.port.outbound.ws_message_port import WsMessagePort

from common.utils.time_utils import create_from_second_now_to_int
from common.core.logger import get_logger
from tldextract import tldextract
import traceback
import time
import os
import re
import json
import PIL.Image
import io
import asyncio
from datetime import datetime

logger = get_logger(__name__)

class BrowserAgent(AgentInstance):

    def __init__(
        self,
        generators_port: GeneratorsPort,
        llm_generator: LLMGenerator,
        ws_message_port: WsMessagePort,
        conversation_port: ConversationPort,
        tools_port: ToolsPort,
    ):
        super().__init__(llm_generator, generators_port, ws_message_port, conversation_port, tools_port)

        # url状态管理
        self._last_rejected_url: Optional[str] = None # 最后拒绝的url
        self.url_statuses: Dict[str, UrlStatus] | None = None
        self.url_block_list: List[str] | None = None
        self._url_status_manager: UrlStatusManager = UrlStatusManager(
            url_statuses=self.url_statuses, url_block_list=self.url_block_list
        )

        # 文件下载处理
        def _download_handler(download: Download) -> None:
            self._last_download = download
        self._download_handler = _download_handler

        # runtime
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self.downloads_folder: str = "downloads"
        self.debug_dir: str = "debug_dir"
        self.browser_screenshot_dir: str = "browser_screenshot"
        self.browser: Optional[PlaywrightBrowser] = None # 浏览器对象
        self.start_page: str = "https://www.baidu.com" # 开始页面
        self.to_save_screenshots: bool = True # 是否保存截图
        self.single_tab_mode: bool = False
        self.did_lazy_init: bool = False
        self.browser = LocalPlaywrightBrowser(headless=False)
        # 拉伸截图，适应大模型的约束
        self.MLM_HEIGHT = 765
        self.MLM_WIDTH = 1224
        # 使用工具名列表
        self.use_tools_name_list: List[str] = []
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

        self._playwright_controller: Optional[PlaywrightController] = None

    async def lazy_init(self, config: Dict[str, Any]) -> None:
        if self.did_lazy_init:
            return
        self._playwright_controller = PlaywrightController(
            animate_actions=False, # 动画
            downloads_folder=self.downloads_folder, # 下载文件夹
            viewport_width=1440, # 窗口宽
            viewport_height=1440, # 窗口高
            _download_handler=self._download_handler, # 下载执行器
            to_resize_viewport=True, # 调整窗口大小
            single_tab_mode=self.single_tab_mode, # 单tab模式
            url_status_manager=self._url_status_manager, # url管理器
            url_validation_callback=self._check_url_and_generate_msg, # url检查器
        )
        await self.browser.__aenter__()
        self._context = self.browser.browser_context
        # Create the page
        assert self._context is not None
        self._context.set_default_timeout(20000)  # 20 sec
        self._page = None
        self._page = await self._context.new_page()  # 打开新页面
        await self._playwright_controller.on_new_page(self._page)  # 配置当前页面的控制器

        # 设置初始页面
        async def handle_new_page(new_pg: Page) -> None:
            # last resort on new tabs
            assert new_pg is not None
            assert self._page is not None
            await new_pg.wait_for_load_state("domcontentloaded")
            new_url = new_pg.url
            await new_pg.close()
            await self._playwright_controller.visit_page(self._page, new_url)

        if self.single_tab_mode:  # 单tab模式确保关闭所有选项卡并指向
            self._context.on("page", lambda new_pg: handle_new_page(new_pg))

        try:
            await self._playwright_controller.visit_page(self._page, self.start_page)
        except Exception:
            traceback.print_exc()

    def execute(self, history_message_list: List[ChatStreamingChunk], payload: Dict[str, Any], client_id: str) -> None:
        content = payload["prompt"]
        message_list: List[ChatStreamingChunk] = []
        # 构建系统提示词
        system_chunk: ChatStreamingChunk = asyncio.run(self._make_system_message())
        message_list.append(system_chunk)
        # 拼接对话历史
        message_list.extend(history_message_list)
        text_prompt, som_screenshot, screenshot, rects, element_id_mapping = asyncio.run(self._load_pagr_info(message=content))
        # 拼接页面状态提示词
        user_chunk: ChatStreamingChunk = asyncio.run(self._make_user_message(text_prompt=text_prompt, som_screenshot=som_screenshot, screenshot=screenshot))
        message_list.append(user_chunk)
        # 发起大模型请求
        # 获取工具
        all_tools = asyncio.run(self.tools_port.load_tools(group_name='browser', tool_type=ToolType.LOCAL))
        # 匹配使用的工具
        tool_call_list = []
        # # 完整结果
        full_content = ""
        for chunk in self.generators_port.generate_event(llm_generator=self.llm_generator, messages=message_list, tools=all_tools):
            # 工具调用
            if chunk.finish_reason == 'tool_calls':
                for tool_call in chunk.tool_calls:
                    tool_call_list.append(
                        {
                            "id": tool_call.id,
                            "name": tool_call.name,
                            "description": tool_call.description,
                            "mcp_server_name": None,
                            "group_name": tool_call.group_name,
                            "arguments": tool_call.arguments,
                        }
                    )
                print(chunk)
        if tool_call_list: # 工具调用逻辑
            data={
                "id": create_uuid(),
                "conversation_id": self.info.conversation_id,
                "dialog_segment_id": self.info.dialog_segment_id,
                "generator_id": self.info.generator_id,
                "model": self.llm_generator.model,
                "created": create_from_second_now_to_int(),
                "tool_calls": tool_call_list
            }
            tool_instance_list: List[ToolInstance] = ToolInstance.from_dict(data)
            # 保存工具实例 TODO
            # 执行工具并保存结果
            asyncio.run(self._tools_call_result(tool_instance_list, rects, element_id_mapping))

    async def _tools_call_result(self, tool_instance_list: List[ToolInstance], rects: Dict[str, InteractiveRegion], element_id_mapping: Dict[str, str]):
        tool_call_task_list = []
        for tool_instance in tool_instance_list:
            tool_call_task_list.append(self._tools_call(tool_instance, rects, element_id_mapping))
            logger.info(f"需要调用工具：{tool_instance.tool_call_id}-{tool_instance.name}-{tool_instance.arguments}")
        results = await asyncio.gather(*tool_call_task_list)
        logger.debug(f"工具调用结果：{results}")
        for tool_call_result in results:
            for tool_instance in tool_instance_list:
                #if tool_instance.tool_call_id == tool_call_result['id']:
                    tool_instance.result = tool_call_result['result']
                    # 更新工具调用实例记录的结果
                    # self.tools_port.update_instance(tool_call)
                    print(f"工具调用完成：{tool_instance}")

    async def _tools_call(self, tool_instance: ToolInstance, rects: Dict[str, InteractiveRegion], element_id_mapping: Dict[str, str]):
        func_name = tool_instance.name
        func_args = tool_instance.arguments
        tool_kwargs = {"args": func_args}
        if func_name in [
            "click",
            "input_text",
            "hover",
            "select_option",
            "upload_file",
            "click_full",
        ]:
            tool_kwargs.update(
                {"rects": rects, "element_id_mapping": element_id_mapping}
            )
        # if func_name in ["answer_question", "summarize_page"]:
        #     tool_kwargs["cancellation_token"] = cancellation_token

        tool_func_name = f"_execute_tool_{func_name}"
        print(f"执行方法～！～！～！～！{tool_func_name}")
        tool_func = getattr(self, tool_func_name, None)
        return await tool_func(**tool_kwargs)
        # execute_tool_task = asyncio.create_task(tool_func(**tool_kwargs))
        # return execute_tool_task

    async def _execute_tool_input_text(
        self,
        args: Dict[str, Any],
        rects: Dict[str, InteractiveRegion],
        element_id_mapping: Dict[str, str],
    ) -> str:
        assert "input_field_id" in args
        assert "text_value" in args
        assert "press_enter" in args
        assert "delete_existing_text" in args
        input_field_id: str = str(args["input_field_id"])
        input_field_name = self._target_name(input_field_id, rects)
        input_field_id = element_id_mapping[input_field_id]

        text_value = str(args.get("text_value"))
        press_enter = bool(args.get("press_enter"))
        delete_existing_text = bool(args.get("delete_existing_text"))

        action_description = (
            f"I typed '{text_value}' into '{input_field_name}'."
            if input_field_name
            else f"I typed '{text_value}'."
        )
        assert self._page is not None
        await self._playwright_controller.fill_id(
            self._page,
            input_field_id,
            text_value,
            press_enter,
            delete_existing_text,
        )
        return action_description

    async def _execute_tool_web_search(self, args: Dict[str, Any]) -> str:
        assert self._page is not None
        ret, approved = await self._check_url_and_generate_msg("bing.com")
        if not approved:
            return ret
        query = cast(str, args.get("query"))
        action_description = f"I typed '{query}' into the browser search bar."
        (
            reset_prior_metadata,
            reset_last_download,
        ) = await self._playwright_controller.visit_page(
            self._page,
            f"https://www.bing.com/search?q={quote_plus(query)}&FORM=QBLH",
        )
        if reset_last_download:
            self._last_download = None
        if reset_prior_metadata:
            self._prior_metadata_hash = None
        return action_description

    async def _load_pagr_info(self, message: str) -> Tuple[str, bytes | PIL.Image.Image | io.BufferedIOBase, bytes | PIL.Image.Image | io.BufferedIOBase, Dict[str, InteractiveRegion], Dict[str, str]]:
        # Ask the page for interactive elements, then prepare the state-of-mark screenshot
        rects = await self._playwright_controller.get_interactive_rects(self._page) # 获取交互区域
        viewport = await self._playwright_controller.get_visual_viewport(self._page) # 获取可视窗口
        screenshot = await self._playwright_controller.get_screenshot(self._page) # 页面截图
        # 代标记的图片 窗口可见元素ID列表  窗口上方不可见的元素ID列表 窗口下方不可见的元素ID列表 将显示的ID映射到原始元素ID的mapping
        som_screenshot, visible_rects, rects_above, rects_below, element_id_mapping = (
            add_set_of_mark(screenshot, rects, use_sequential_ids=True)
        )
        # 反转显示的ID映射到原始元素ID的mapping，便于点击操作
        reverse_element_id_mapping = {v: k for k, v in element_id_mapping.items()}
        rects = {reverse_element_id_mapping.get(k, k): v for k, v in rects.items()}
        # 保存截图到debug_dir
        if self.to_save_screenshots and self.debug_dir is not None:
            current_timestamp = "_" + int(time.time()).__str__()
            screenshot_png_name = "screenshot_som" + current_timestamp + ".png"
            som_screenshot.save(os.path.join(self.debug_dir, screenshot_png_name))
            logger.info(f"Screenshot saved to {self.debug_dir}/{screenshot_png_name}")
        # 获取标签页信息
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

        # 焦点提示
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

        # 将窗口中的可见目标列表格式化为字符串：visible_targets
        visible_targets = (
                "\n".join(self._format_target_list(visible_rects, rects)) + "\n\n"
        )

        # 将窗口中的不可见目标格式化为字符串，存入other_targets列表
        other_targets: List[str] = []
        other_targets.extend(self._format_target_list(rects_above, rects))
        other_targets.extend(self._format_target_list(rects_below, rects))

        # 提取不可见元素的json？
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
        # 检索浏览器视口的文本概况内容
        webpage_text = await self._playwright_controller.get_visible_text(self._page)
        # 构建页面描述及任务目标提示词
        text_prompt = self.info.agent_prompts['WEB_SURFER_TOOL_PROMPT'].format(
            tabs_information=tabs_information_str,
            last_outside_message=message,
            webpage_text=webpage_text,
            url=self._page.url,
            visible_targets=visible_targets,
            consider_screenshot="Consider the following screenshot of a web browser,",
            other_targets_str=other_targets_str,
            focused_hint=focused_hint
        ).strip()
        return text_prompt, som_screenshot, screenshot, rects, element_id_mapping

    async def _make_system_message(self) -> ChatStreamingChunk:
        date_today = datetime.now().strftime("%Y-%m-%d")
        text_system = self.info.agent_prompts['WEB_SURFER_SYSTEM_MESSAGE'].format(
            date_today=date_today,
        ).strip()
        return ChatStreamingChunk.from_system(message=text_system)

    async def _make_user_message(
        self,
        text_prompt: str,
        som_screenshot: bytes | PIL.Image.Image | io.BufferedIOBase,
        screenshot: bytes | PIL.Image.Image | io.BufferedIOBase
    ) -> ChatStreamingChunk:
        # 拉伸截图
        scaled_som_screenshot = som_screenshot.resize(
            (self.MLM_WIDTH, self.MLM_HEIGHT)
        )
        screenshot_file = PIL.Image.open(io.BytesIO(screenshot))
        scaled_screenshot = screenshot_file.resize(
            (self.MLM_WIDTH, self.MLM_HEIGHT)
        )
        # 保存图片
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
        # 转换base64
        screenshot_png_base64_image = open_and_base64(screenshot_png_url)
        screenshot_som_png_base64_image = open_and_base64(screenshot_som_png_url)
        content = [
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
        return ChatStreamingChunk.from_user(message=content)

    # def _send_llm_event(self, client_id: str, context_message_list: List[ChatStreamingChunk]):
    #     """发送大模型请求事件"""
    #     event = Event.from_init(
    #         event_type=EventType.USER_MESSAGE,
    #         event_sub_type=EventSubType.MESSAGE,
    #         client_id=client_id,
    #         source=EventSource.AGENT,
    #         data={
    #             "id": create_uuid(),
    #             "dialog_segment_id": self.info.dialog_segment_id,
    #             "conversation_id": self.info.conversation_id,
    #             "generator_id": self.info.generator_id,
    #         },
    #         payload={
    #             "agent_instance_id": self.info.instance_id,
    #             "json_result": False,
    #             "mcp_name_list": [],
    #             "tools_group_name_list": self.use_tools_name_list,
    #             "context_message_list": context_message_list,
    #         }
    #     )
    #     EventPort.get_event_port().emit_event(event)
    #     logger.info(
    #         f"[{self.info.name}]Agent实例[{self.info.instance_id}],发送LLM请求事件[{self.info.dialog_segment_id}]")

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
                self._url_status_manager.set_url_status(domain, URL_REJECTED)

            self._last_rejected_url = url
            return (
                f"I am not allowed to access the website {url} because it is not in the list of websites I can access and the user has declined to allow it.",
                False,
            )
        return "", True

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