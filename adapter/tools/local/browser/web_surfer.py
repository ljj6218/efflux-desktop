# import asyncio
# import tldextract
# from typing import List, Dict, Optional, Tuple, AsyncGenerator, Union
# from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk
# import json
# from playwright.async_api import (
#     BrowserContext,
#     Download,
#     Page,
# )
#
# from common.utils.playwright.browser import PlaywrightBrowser, VncDockerPlaywrightBrowser
#
# # from ...approval_guard import (
# #     ApprovalGuardContext,
# #     BaseApprovalGuard,
# #     MaybeRequiresApproval,
# # )
#
# # from ._events import WebSurferEvent
# from .tools_prompts import (
#     WEB_SURFER_OCR_PROMPT,
#     WEB_SURFER_QA_PROMPT,
#     WEB_SURFER_QA_SYSTEM_MESSAGE,
#     WEB_SURFER_TOOL_PROMPT,
#     WEB_SURFER_SYSTEM_MESSAGE,
#     WEB_SURFER_NO_TOOLS_PROMPT,
# )
#
# from common.utils.playwright.playwright_state import (
#     BrowserState,
#     save_browser_state,
#     load_browser_state,
# )
#
# from .browser_tools_definitions import (
#     TOOL_CLICK,
#     TOOL_HISTORY_BACK,
#     TOOL_HOVER,
#     TOOL_PAGE_DOWN,
#     TOOL_PAGE_UP,
#     TOOL_READ_PAGE_AND_ANSWER,
#     TOOL_SLEEP,
#     TOOL_TYPE,
#     TOOL_VISIT_URL,
#     TOOL_WEB_SEARCH,
#     TOOL_STOP_ACTION,
#     TOOL_SELECT_OPTION,
#     TOOL_CREATE_TAB,
#     TOOL_SWITCH_TAB,
#     TOOL_CLOSE_TAB,
#     TOOL_KEYPRESS,
#     TOOL_REFRESH_PAGE,
# )
#
# from ...tools import get_tool_metadata, ToolMetadata
# from common.utils.playwright.types import InteractiveRegion
# from common.utils.playwright.playwright_controller import PlaywrightController
# from common.utils.playwright.playwright_state import (
#     BrowserState,
#     save_browser_state,
#     load_browser_state,
# )
# from common.utils.playwright.url_status_manager import (
#     UrlStatusManager,
#     UrlStatus,
#     URL_ALLOWED,
#     URL_REJECTED,
# )
#
#
# from common.core.logger import get_logger
# # 设置日志
# logger = get_logger(__name__)
#
# from application.port.outbound.generators_port import GeneratorsPort
# from application.domain.generators.generator import LLMGenerator
# from application.domain.generators.tools import Tool
#
# from adapter.tools.tools import ToolSchema
#
# from common.utils.playwright.browser.local_playwright_browser import LocalPlaywrightBrowser, LocalPlaywrightBrowserConfig
#
#
# class WebSurfer:
#     def __init__(
#             self,
#             generators_port: GeneratorsPort,
#             name: str,
#             start_page: str = "about:blank",
#
#             animate_actions: bool = False,
#             downloads_folder: str | None = None,
#             viewport_width: int = 1440,
#             viewport_height: int = 1440,
#             to_resize_viewport: bool = True,
#             single_tab_mode: bool = False,
#             url_statuses: Optional[Dict[str, UrlStatus]] = None,
#             url_block_list: Optional[List[str]] = None,
#             use_action_guard: bool = False
#     ):
#         self.animate_actions = animate_actions
#         self.downloads_folder = downloads_folder
#         self.viewport_width = viewport_width
#         self.viewport_height = viewport_height
#         self._last_download: Download | None = None
#         self.to_resize_viewport = to_resize_viewport
#         self.single_tab_mode = single_tab_mode
#
#         self.use_action_guard = use_action_guard
#
#         self._last_rejected_url: str | None = None
#
#         # Define the download handler
#         def _download_handler(download: Download) -> None:
#             self._last_download = download
#
#         self._download_handler = _download_handler
#
#         self._url_status_manager: UrlStatusManager = UrlStatusManager(
#             url_statuses=url_statuses, url_block_list=url_block_list
#         )
#
#         # Define the Playwright controller that handles the browser interactions
#         self._playwright_controller = PlaywrightController(
#             animate_actions=self.animate_actions,
#             downloads_folder=self.downloads_folder,
#             viewport_width=self.viewport_width,
#             viewport_height=self.viewport_height,
#             _download_handler=self._download_handler,
#             to_resize_viewport=self.to_resize_viewport,
#             single_tab_mode=self.single_tab_mode,
#             url_status_manager=self._url_status_manager,
#             url_validation_callback=self._check_url_and_generate_msg,
#         )
#
#         self._browser = LocalPlaywrightBrowser.from_config(
#             LocalPlaywrightBrowserConfig(headless=False, enable_downloads=True, persistent_context=True,
#                                          browser_data_dir="/Users/siyong/PycharmProjects/efflux_desktop/bb")
#         )
#
#         self.default_tools: List[ToolSchema] = [
#             TOOL_STOP_ACTION,
#             TOOL_VISIT_URL,
#             TOOL_WEB_SEARCH,
#             TOOL_CLICK,
#             TOOL_TYPE,
#             TOOL_READ_PAGE_AND_ANSWER,
#             TOOL_SLEEP,
#             TOOL_HOVER,
#             TOOL_HISTORY_BACK,
#             TOOL_KEYPRESS,
#             TOOL_REFRESH_PAGE,
#             # TOOL_CLICK_FULL,
#         ]
#
#
#         self.generators_port = generators_port
#         self.name = name
#
#         # Playwright 浏览器初始化
#         self._start_page = start_page
#         self._context = None
#         self._page = None
#
#         # 状态管理
#         self._url_status_manager = UrlStatusManager()
#
#     async def _check_url_and_generate_msg(self, url: str) -> Tuple[str, bool]:
#         """Returns a message to caller if the URL is not allowed and a boolean indicating if the user has approved the URL."""
#         # TODO: Hacky check to see if the URL was aborted. Find a better way to do this
#         if url == "chrome-error://chromewebdata/":
#             if self._last_rejected_url is not None:
#                 last_rejected_url = self._last_rejected_url
#                 self._last_rejected_url = None
#                 return (
#                     f"I am not allowed to access the website {last_rejected_url} because it is not in the list of websites I can access and the user has declined to approve it.",
#                     False,
#                 )
#
#         if self._url_status_manager.is_url_blocked(url):
#             return (
#                 f"I am not allowed to access the website {url} because has been blocked.",
#                 False,
#             )
#
#         if not self._url_status_manager.is_url_allowed(url):
#             if not self._url_status_manager.is_url_rejected(url):
#                 # tldextract will only recombine entries with valid, registered hostnames. We'll just use the straight url for anything else.
#                 domain = tldextract.extract(url).fqdn
#                 if not domain:
#                     domain = url
#                 response = False
#                 # 高危网站安全防护 TODO
#                 # if self.action_guard is not None:
#                 #     # The content string here is important because the UI is checking for specific wording to detect the URL approval request
#                 #     request_message = TextMessage(
#                 #         source=self.name,
#                 #         content=f"The website {url} is not allowed. Would you like to allow the domain {domain} for this session?",
#                 #     )
#                 #     response = await self.action_guard.get_approval(request_message)
#                 if response:
#                     self._url_status_manager.set_url_status(domain, URL_ALLOWED)
#                     return (
#                         "",
#                         True,
#                     )
#                 else:
#                     self._url_status_manager.set_url_status(domain, URL_REJECTED)
#
#             self._last_rejected_url = url
#             return (
#                 f"I am not allowed to access the website {url} because it is not in the list of websites I can access and the user has declined to allow it.",
#                 False,
#             )
#         return "", True
#
#
#
#
#
#     async def lazy_init(self) -> None:
#         """初始化浏览器，获取浏览器页面"""
#         if self._page is not None:
#             return
#
#         # 启动浏览器
#         await self._browser.__aenter__()
#
#         # 创建新的浏览器上下文
#         self._context = self._browser.browser_context
#
#         # 创建新页面
#         assert self._context is not None
#         self._context.set_default_timeout(20000) # 超时时间
#
#         self._page = await self._context.new_page()
#
#         # 跳转到初始页面
#         await self._page.goto(self.start_page)
#         logger.info(f"WebSurfer started on page: {self.start_page}")
#
#         try:
#             await self._playwright_controller.visit_page(self._page, self.start_page)
#         except Exception:
#             pass
#
#
#     async def on_messages_stream(self, chunk_list: List[ChatStreamingChunk], generator: LLMGenerator) -> AsyncGenerator[ChatStreamingChunk, None]:
#         tool_list: List[Tool] = []
#         for default_tool in self.default_tools:
#             tool_list.append(Tool(name=default_tool["name"], description=default_tool['description'], input_schema=default_tool['parameters'], mcp_server_name="local"))
#
#
#         for chunk in self.generators_port.generate_event(llm_generator=generator, messages=chunk_list, tools=tool_list):
#             print(chunk)
#
#     # async def _get_llm_response(
#     #         self, cancellation_token: Optional[CancellationToken] = None
#     # ) -> tuple[
#     #     Union[str, List[FunctionCall]],
#     #     Dict[str, InteractiveRegion],
#     #     List[ToolSchema],
#     #     Dict[str, str],
#     #     bool,
#     # ]:
#     #     """Generate the next action to take based on the current page state.
#     #
#     #     Args:
#     #         cancellation_token (CancellationToken, optional): Token to cancel the operation. Default: None
#     #
#     #     Returns:
#     #         Tuple containing:
#     #             - str | List[FunctionCall]: The model's response (text or function calls)
#     #             - Dict[str, InteractiveRegion]: Dictionary of interactive page elements
#     #             - List[ToolSchema]: String of available tool names
#     #             - Dict[str, str]: Mapping of element IDs
#     #             - bool: Boolean indicating if tool execution is needed
#     #     """
#     #
#     #     # Lazy init, initialize the browser and the page on the first generate reply only
#     #     if not self.did_lazy_init:
#     #         await self.lazy_init()
#     #
#     #     try:
#     #         assert self._page is not None
#     #         assert (
#     #                 await self._playwright_controller.get_interactive_rects(self._page)
#     #                 is not None
#     #         )
#     #     except Exception as e:
#     #         # open a new tab and point it to about:blank
#     #         self.logger.error(f"Page is not accessible, creating a new one: {e}")
#     #         assert self._context is not None
#     #         self._page = await self._playwright_controller.create_new_tab(
#     #             self._context, "about:blank"
#     #         )
#     #
#     #     # Clone the messages to give context, removing old screenshots
#     #     history: List[LLMMessage] = []
#     #     date_today = datetime.now().strftime("%Y-%m-%d")
#     #     history.append(
#     #         SystemMessage(
#     #             content=WEB_SURFER_SYSTEM_MESSAGE.format(date_today=date_today)
#     #         )
#     #     )
#     #     # Keep images only for user messages, remove from others
#     #     filtered_history: List[LLMMessage] = []
#     #     for msg in self._chat_history:
#     #         if isinstance(msg, UserMessage) and msg.source in ["user", "user_proxy"]:
#     #             filtered_history.append(msg)
#     #         else:
#     #             filtered_history.extend(remove_images([msg]))
#     #     history.extend(filtered_history)
#     #
#     #     # Ask the page for interactive elements, then prepare the state-of-mark screenshot
#     #     rects = await self._playwright_controller.get_interactive_rects(self._page)
#     #     viewport = await self._playwright_controller.get_visual_viewport(self._page)
#     #     screenshot = await self._playwright_controller.get_screenshot(self._page)
#     #     som_screenshot, visible_rects, rects_above, rects_below, element_id_mapping = (
#     #         add_set_of_mark(screenshot, rects, use_sequential_ids=True)
#     #     )
#     #     # element_id_mapping is a mapping of new ids to original ids in the page
#     #     # we need to reverse it to get the original ids from the new ids
#     #     # for each element we click, we need to use the original id
#     #     reverse_element_id_mapping = {v: k for k, v in element_id_mapping.items()}
#     #     rects = {reverse_element_id_mapping.get(k, k): v for k, v in rects.items()}
#     #
#     #     if self.to_save_screenshots and self.debug_dir is not None:
#     #         current_timestamp = "_" + int(time.time()).__str__()
#     #         screenshot_png_name = "screenshot_som" + current_timestamp + ".png"
#     #         som_screenshot.save(os.path.join(self.debug_dir, screenshot_png_name))
#     #         self.logger.debug(
#     #             WebSurferEvent(
#     #                 source=self.name,
#     #                 url=self._page.url,
#     #                 message="Screenshot: " + screenshot_png_name,
#     #             )
#     #         )
#     #
#     #     # Get the tabs information
#     #     tabs_information_str = ""
#     #     num_tabs = 1
#     #     if not self.single_tab_mode and self._context is not None:
#     #         num_tabs, tabs_information_str = await self.get_tabs_info()
#     #         tabs_information_str = f"There are {num_tabs} tabs open. The tabs are as follows:\n{tabs_information_str}"
#     #
#     #     # What tools are available?
#     #     tools = self.default_tools.copy()
#     #
#     #     # If not in single tab mode, always allow creating new tabs
#     #     if not self.single_tab_mode:
#     #         if TOOL_CREATE_TAB not in tools:
#     #             tools.append(TOOL_CREATE_TAB)
#     #
#     #     # If there are multiple tabs, we can switch between them and close them
#     #     if not self.single_tab_mode and num_tabs > 1:
#     #         tools.append(TOOL_SWITCH_TAB)
#     #         tools.append(TOOL_CLOSE_TAB)
#     #
#     #     # We can scroll up
#     #     if viewport["pageTop"] > 5:
#     #         tools.append(TOOL_PAGE_UP)
#     #
#     #     # Can scroll down
#     #     if (viewport["pageTop"] + viewport["height"] + 5) < viewport["scrollHeight"]:
#     #         tools.append(TOOL_PAGE_DOWN)
#     #
#     #     # Add select_option tool only if there are option elements
#     #     if any(rect.get("role") == "option" for rect in rects.values()):
#     #         tools.append(TOOL_SELECT_OPTION)
#     #
#     #     # Add upload_file tool only if there are file input elements
#     #     # if any(rect.get("tag_name") == "input, type=file" for rect in rects.values()):
#     #     #    tools.append(TOOL_UPLOAD_FILE)
#     #
#     #     # Focus hint
#     #     focused = await self._playwright_controller.get_focused_rect_id(self._page)
#     #     focused = reverse_element_id_mapping.get(focused, focused)
#     #
#     #     focused_hint = ""
#     #     if focused:
#     #         name = self._target_name(focused, rects)
#     #         if name:
#     #             name = f"(and name '{name}') "
#     #
#     #         role = "control"
#     #         try:
#     #             role = rects[focused]["role"]
#     #         except KeyError:
#     #             pass
#     #
#     #         focused_hint = f"\nThe {role} with ID {focused} {name}currently has the input focus.\n\n"
#     #
#     #     # Everything visible
#     #     visible_targets = (
#     #             "\n".join(self._format_target_list(visible_rects, rects)) + "\n\n"
#     #     )
#     #
#     #     # Everything else
#     #     other_targets: List[str] = []
#     #     other_targets.extend(self._format_target_list(rects_above, rects))
#     #     other_targets.extend(self._format_target_list(rects_below, rects))
#     #
#     #     if len(other_targets) > 0:
#     #         # Extract just the names from the JSON strings
#     #         other_target_names: List[str] = []
#     #         for target in other_targets:
#     #             try:
#     #                 target_dict = json.loads(target)
#     #                 name = target_dict.get("name", "")
#     #                 role = target_dict.get("role", "")
#     #                 other_target_names.append(name if name else f"{role} control")
#     #             except json.JSONDecodeError:
#     #                 continue
#     #
#     #         other_targets_str = (
#     #                 "Some additional valid interaction targets (not shown, you need to scroll to interact with them) include:\n"
#     #                 + ", ".join(other_target_names[:30])
#     #                 + "\n\n"
#     #         )
#     #     else:
#     #         other_targets_str = ""
#     #
#     #     tool_names = WebSurfer._tools_to_names(tools)
#     #
#     #     webpage_text = await self._playwright_controller.get_visible_text(self._page)
#     #
#     #     if not self.json_model_output:
#     #         text_prompt = WEB_SURFER_TOOL_PROMPT.format(
#     #             tabs_information=tabs_information_str,
#     #             last_outside_message=self._last_outside_message,
#     #             webpage_text=webpage_text,
#     #             url=self._page.url,
#     #             visible_targets=visible_targets,
#     #             consider_screenshot="Consider the following screenshot of a web browser,"
#     #             if self.is_multimodal
#     #             else "Consider the following webpage",
#     #             other_targets_str=other_targets_str,
#     #             focused_hint=focused_hint,
#     #             tool_names=tool_names,
#     #         ).strip()
#     #     else:
#     #         text_prompt = WEB_SURFER_NO_TOOLS_PROMPT.format(
#     #             tabs_information=tabs_information_str,
#     #             last_outside_message=self._last_outside_message,
#     #             webpage_text=webpage_text,
#     #             url=self._page.url,
#     #             visible_targets=visible_targets,
#     #             consider_screenshot="Consider the following screenshot of a web browser,"
#     #             if self.is_multimodal
#     #             else "Consider the following webpage",
#     #             other_targets_str=other_targets_str,
#     #             focused_hint=focused_hint,
#     #         ).strip()
#     #
#     #     if self.is_multimodal:
#     #         # Scale the screenshot for the MLM, and close the original
#     #         scaled_som_screenshot = som_screenshot.resize(
#     #             (self.MLM_WIDTH, self.MLM_HEIGHT)
#     #         )
#     #         screenshot_file = PIL.Image.open(io.BytesIO(screenshot))
#     #         scaled_screenshot = screenshot_file.resize(
#     #             (self.MLM_WIDTH, self.MLM_HEIGHT)
#     #         )
#     #         som_screenshot.close()
#     #         screenshot_file.close()
#     #
#     #         # Add the multimodal message and make the request
#     #         history.append(
#     #             UserMessage(
#     #                 content=[
#     #                     text_prompt,
#     #                     AGImage.from_pil(scaled_som_screenshot),
#     #                     AGImage.from_pil(scaled_screenshot),
#     #                 ],
#     #                 source=self.name,
#     #             )
#     #         )
#     #     else:
#     #         history.append(
#     #             UserMessage(
#     #                 content=text_prompt,
#     #                 source=self.name,
#     #             )
#     #         )
#     #
#     #     # Re-initialize model context to meet token limit quota
#     #     try:
#     #         await self._model_context.clear()
#     #         for msg in history:
#     #             await self._model_context.add_message(msg)
#     #         token_limited_history = await self._model_context.get_messages()
#     #     except Exception:
#     #         token_limited_history = history
#     #
#     #     if not self.json_model_output:
#     #         create_args: Dict[str, Any] | None = None
#     #         if self._model_client.model_info["family"] in [
#     #             "gpt-4o",
#     #             "gpt-41",
#     #             "gpt-45",
#     #             "o3",
#     #             "o4",
#     #         ]:
#     #             create_args = {
#     #                 "tool_choice": "required",
#     #             }
#     #             if self.multiple_tools_per_call:
#     #                 create_args["parallel_tool_calls"] = True
#     #         if create_args is not None:
#     #             response = await self._model_client.create(
#     #                 token_limited_history,
#     #                 tools=tools,
#     #                 cancellation_token=cancellation_token,
#     #                 extra_create_args=create_args,
#     #             )
#     #         else:
#     #             response = await self._model_client.create(
#     #                 token_limited_history,
#     #                 tools=tools,
#     #                 cancellation_token=cancellation_token,
#     #             )
#     #     else:
#     #         response = await self._model_client.create(
#     #             token_limited_history,
#     #             cancellation_token=cancellation_token,
#     #         )
#     #     self.model_usage.append(response.usage)
#     #     self._last_download = None
#     #     if not self.json_model_output:
#     #         to_execute_tool = isinstance(response.content, list)
#     #         return (
#     #             response.content,
#     #             rects,
#     #             tools,
#     #             element_id_mapping,
#     #             to_execute_tool,
#     #         )
#     #     else:
#     #         try:
#     #             # check if first line is `json
#     #             response_content = response.content
#     #             assert isinstance(response_content, str)
#     #             if response_content.startswith("```json"):
#     #                 # remove first and last line
#     #                 response_lines = response_content.split("\n")
#     #                 response_lines = response_lines[1:-1]
#     #                 response_content = "\n".join(response_lines)
#     #
#     #             json_response = json.loads(response_content)
#     #             tool_name = json_response["tool_name"]
#     #             tool_args = json_response["tool_args"]
#     #             tool_args["explanation"] = json_response["explanation"]
#     #             function_call = FunctionCall(
#     #                 id="json_response", name=tool_name, arguments=json.dumps(tool_args)
#     #             )
#     #             return [function_call], rects, tools, element_id_mapping, True
#     #         except Exception as e:
#     #             error_msg = f"Failed to parse JSON response: {str(e)}. Response was: {response.content}"
#     #             return error_msg, rects, tools, element_id_mapping, False
#
#     async def execute_tool(self, tool_name: str, args: Dict):
#         """执行指定的浏览器工具"""
#         if tool_name == TOOL_VISIT_URL:
#             await self._execute_tool_visit_url(args)
#         elif tool_name == TOOL_CLICK:
#             await self._execute_tool_click(args)
#         elif tool_name == TOOL_PAGE_DOWN:
#             await self._execute_tool_page_down(args)
#         elif tool_name == TOOL_PAGE_UP:
#             await self._execute_tool_page_up(args)
#         elif tool_name == TOOL_HISTORY_BACK:
#             await self._execute_tool_history_back(args)
#         elif tool_name == TOOL_REFRESH_PAGE:
#             await self._execute_tool_refresh_page(args)
#
#     async def on_messages(self, messages: List[str]) -> None:
#         """处理模型生成的指令"""
#         # 处理每一条消息
#         for message in messages:
#             response = await self.process_request(message)
#             tool_name, args = response  # 假设模型返回了工具和参数
#             await self.execute_tool(tool_name, args)
#
#     async def process_request(self, user_message: str) -> tuple:
#         """模拟处理用户请求并生成响应"""
#         logger.info(f"Processing message: {user_message}")
#         # 模拟返回工具名称和参数
#         return TOOL_VISIT_URL, {"url": "https://example.com"}
#
#     async def _execute_tool_visit_url(self, args: Dict) -> str:
#         """访问指定的 URL"""
#         url = args["url"]
#         await self._page.goto(url)
#         logger.info(f"Visited URL: {url}")
#         return f"Visited {url}"
#
#     async def _execute_tool_click(self, args: Dict) -> str:
#         """点击元素"""
#         selector = args["selector"]
#         element = await self._page.query_selector(selector)
#         if element:
#             await element.click()
#             logger.info(f"Clicked element: {selector}")
#             return f"Clicked {selector}"
#         else:
#             logger.warning(f"Element {selector} not found!")
#             return f"Element {selector} not found"
#
#     async def _execute_tool_page_down(self, args: Dict) -> str:
#         """滚动页面向下"""
#         await self._page.keyboard.press("PageDown")
#         logger.info("Scrolled down the page")
#         return "Scrolled down the page"
#
#     async def _execute_tool_page_up(self, args: Dict) -> str:
#         """滚动页面向上"""
#         await self._page.keyboard.press("PageUp")
#         logger.info("Scrolled up the page")
#         return "Scrolled up the page"
#
#     async def _execute_tool_history_back(self, args: Dict) -> str:
#         """返回历史页面"""
#         await self._page.go_back()
#         logger.info("Went back to the previous page")
#         return "Went back to the previous page"
#
#     async def _execute_tool_refresh_page(self, args: Dict) -> str:
#         """刷新当前页面"""
#         await self._page.reload()
#         logger.info("Refreshed the page")
#         return "Refreshed the page"
#
#     async def save_state(self) -> Dict:
#         """保存当前的 WebSurfer 状态"""
#         browser_state = await save_browser_state(self._context, self._page)
#         state = {
#             "browser_state": browser_state,
#         }
#         return state
#
#     async def load_state(self, state: Dict) -> None:
#         """加载之前保存的状态"""
#         browser_state = state.get("browser_state")
#         if browser_state:
#             await load_browser_state(self._context, browser_state)
#
#     async def close(self) -> None:
#         """关闭浏览器"""
#         if self._page:
#             await self._page.close()
#         await self._browser.__aexit__(None, None, None)
#         logger.info("Closed WebSurfer and browser.")
#
#
