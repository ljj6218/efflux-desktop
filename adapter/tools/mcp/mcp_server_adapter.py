from typing import List, Optional

from application.domain.mcp_server import MCPServer
from application.port.outbound.mcp_server_port import MCPServerPort
from common.core.container.annotate import component
from common.utils.json_file_util import JSONFileUtil

@component
class MCPServerAdapter(MCPServerPort):

    mcp_servers_hub_file_url = "adapter/tools/mcp/mcp_servers.json"
    user_mcp_servers_file_url = "mcp_servers.json"

    def apply(self, mcp_server: MCPServer) -> str:
        user_mcp_servers = JSONFileUtil(self.user_mcp_servers_file_url)
        mcp_server_dict: dict = mcp_server.model_dump()
        if "server_description" in mcp_server_dict:
            del mcp_server_dict["server_description"]
        if "applied" in mcp_server_dict:
            del mcp_server_dict["applied"]
        if "server_name" in mcp_server_dict:
            del mcp_server_dict["server_name"]
        user_mcp_servers.update_key(mcp_server.server_name, mcp_server_dict)
        return mcp_server.server_name

    def load(self, server_name: str) -> Optional[MCPServer]:
        mcp_servers_hub = JSONFileUtil(self.mcp_servers_hub_file_url)
        user_mcp_servers = JSONFileUtil(self.user_mcp_servers_file_url)
        mcp_server_dict = mcp_servers_hub.read_key(server_name)
        if not mcp_server_dict:
            return None
        mcp_server: MCPServer = MCPServer.model_validate(mcp_server_dict)
        # 已启用mcp_server属性设置
        user_mcp_server = user_mcp_servers.read_key(server_name)
        if user_mcp_server:
            mcp_server.execute_authorization = user_mcp_server['execute_authorization']
            mcp_server.applied = True
        return mcp_server

    def add(self, mcp_server: MCPServer) -> MCPServer:
        mcp_servers_hub = JSONFileUtil(self.mcp_servers_hub_file_url)
        mcp_server_dict = mcp_server.model_dump()
        if "applied" in mcp_server_dict:
            del mcp_server_dict["applied"]
        if "enabled" in mcp_server_dict:
            del mcp_server_dict["enabled"]
        if "execute_authorization" in mcp_server_dict:
            del mcp_server_dict["execute_authorization"]
        mcp_servers_hub.update_key(mcp_server.server_name, mcp_server_dict)
        return mcp_server

    def remove(self, server_name: str) -> str:
        mcp_servers_hub = JSONFileUtil(self.mcp_servers_hub_file_url)
        mcp_servers_hub.delete(server_name)
        return server_name

    def load_applied(self, server_name: str) -> Optional[MCPServer]:
        user_mcp_servers = JSONFileUtil(self.user_mcp_servers_file_url)
        mcp_server_dict = user_mcp_servers.read_key(server_name)
        if not mcp_server_dict:
            return None
        mcp_server: MCPServer = MCPServer.model_validate(mcp_server_dict)
        mcp_server.applied = True
        mcp_server.server_name = server_name
        return mcp_server

    def load_applied_list(self, server_name: Optional[str] = None) -> List[MCPServer]:
        user_mcp_servers = JSONFileUtil(self.user_mcp_servers_file_url)
        mcp_server_list: List[MCPServer] = []
        for mcp_name in user_mcp_servers.read().keys():
            if server_name and not mcp_name.startswith(server_name):
                continue
            mcp_server_dict = user_mcp_servers.read_key(mcp_name)
            mcp_server: MCPServer = MCPServer.model_validate(mcp_server_dict)
            mcp_server.applied = True
            mcp_server.server_name = mcp_name
            mcp_server_list.append(mcp_server)
        return mcp_server_list

    def load_enabled_list(self, server_name: Optional[str] = None) -> List[MCPServer]:
        user_mcp_servers = JSONFileUtil(self.user_mcp_servers_file_url)
        mcp_server_list: List[MCPServer] = []
        for mcp_name in user_mcp_servers.read().keys():
            if server_name and not mcp_name.startswith(server_name):
                continue
            mcp_server_dict = user_mcp_servers.read_key(mcp_name)
            if not mcp_server_dict['enabled']:
                continue
            mcp_server: MCPServer = MCPServer.model_validate(mcp_server_dict)
            mcp_server.applied = True
            mcp_server.server_name = mcp_name
            mcp_server_list.append(mcp_server)
        return mcp_server_list

    def cancel_apply(self, server_name: str) -> str:
        user_mcp_servers = JSONFileUtil(self.user_mcp_servers_file_url)
        user_mcp_servers.delete(server_name)
        return server_name

    def load_list(self, server_name: Optional[str] = None, server_tag: Optional[str] = None) -> List[MCPServer]:
        mcp_servers_hub = JSONFileUtil(self.mcp_servers_hub_file_url)
        user_mcp_servers = JSONFileUtil(self.user_mcp_servers_file_url)
        mcp_server_list: List[MCPServer] = []
        for mcp_name in mcp_servers_hub.read().keys():
            mcp_server_dict = mcp_servers_hub.read_key(mcp_name)
            # 标签筛选
            if server_tag:
                if mcp_server_dict['server_tag'] != server_tag:
                    continue
            if server_name and not mcp_name.startswith(server_name):
                continue
            mcp_server: MCPServer = MCPServer.model_validate(mcp_server_dict)
            # 已启用mcp_server属性设置
            user_mcp_server = user_mcp_servers.read_key(mcp_name)
            if user_mcp_server:
                mcp_server.execute_authorization = user_mcp_server['execute_authorization']
                mcp_server.applied = True
            mcp_server_list.append(mcp_server)
        return mcp_server_list

    def is_authorized(self, server_name: str) -> bool:
        user_mcp_servers = JSONFileUtil(self.user_mcp_servers_file_url)
        mcp_server_dict = user_mcp_servers.read_key(server_name)
        if not mcp_server_dict:
            return False
        return mcp_server_dict['execute_authorization']

    def execute_authorization(self, server_name: str, execute_authorization: bool) -> str:
        user_mcp_servers = JSONFileUtil(self.user_mcp_servers_file_url)
        mcp_server_dict = user_mcp_servers.read_key(server_name)
        if mcp_server_dict:
            mcp_server_dict['execute_authorization'] = execute_authorization
            user_mcp_servers.update_key(server_name, mcp_server_dict)
        return server_name

    def enabled(self, server_name: str, enabled: bool) -> str:
        user_mcp_servers = JSONFileUtil(self.user_mcp_servers_file_url)
        mcp_server_dict = user_mcp_servers.read_key(server_name)
        if mcp_server_dict:
            mcp_server_dict['enabled'] = enabled
            user_mcp_servers.update_key(server_name, mcp_server_dict)
        return server_name