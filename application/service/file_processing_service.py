from typing import List, Optional
from common.core.container.annotate import component
from application.domain.file import File, FileChunk
from application.port.outbound.file_port import FilePort
from application.port.outbound.file_vector_port import FileVectorPort
from application.port.outbound.embedding_port import EmbeddingPort
from application.port.outbound.generators_port import GeneratorsPort
from application.port.outbound.vector_model_port import VectorModelPort
import injector
from common.core.logger import get_logger
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownTextSplitter

logger = get_logger(__name__)

@component
class FileProcessingService:

    @injector.inject
    def __init__(
        self,
        file_port: FilePort,
        file_vectordb_port: FileVectorPort,
        embedding_port: EmbeddingPort,
        generators_port: GeneratorsPort,
        vector_model_port: VectorModelPort,
    ):
        self.file_port = file_port
        self.file_vectordb_port = file_vectordb_port
        self.embedding_port = embedding_port
        self.generators_port = generators_port
        self.vector_model_port = vector_model_port

    async def process_file_to_chunks(self, generator_id: str, file_entity: File) -> List[FileChunk]:
        llm_generator = self.generators_port.load_generate(generator_id)
        logger.debug(f"加载的生成器: {llm_generator}")
        embeddings_model_settings_list = self.vector_model_port.list()
        embeddings_model_settings = None

        embeddings_model_settings_list = await self.vector_model_port.list()
        logger.debug(f"嵌入模型设置列表: {embeddings_model_settings_list}")
        if not embeddings_model_settings_list:
            raise ValueError("未找到嵌入模型设置")
        for i in embeddings_model_settings_list:  # 现在可以正常迭代
            print(f"嵌入模型设置: {i}")
            if i.firm == llm_generator.firm:
                embeddings_model_settings = i
        if not embeddings_model_settings:
            raise ValueError(f"未找到对应的嵌入模型设置: {llm_generator.firm}")
        embeddings = self.embedding_port.get_embeddings(embeddings_model_settings)
        return await self.file_vectordb_port.store_chunks(embeddings, file_entity)
