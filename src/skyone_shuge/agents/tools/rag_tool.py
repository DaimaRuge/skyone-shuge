"""
Agent RAG 工具 - 将 RAG 检索能力暴露给 Agent
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

from ...ml.rag import RAGEngine, RAGQuery, SearchMode
from ...services.search_service import SearchService
from ...schemas.search import SearchQuery

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """Agent 工具基类"""
    
    name: str = ""
    description: str = ""
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具逻辑
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
        """
        pass
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """获取参数 JSON Schema（用于 OpenAI Function Calling）"""
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    def to_openai_function(self) -> Dict[str, Any]:
        """转换为 OpenAI Function 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters_schema()
            }
        }


class RAGTool(BaseTool):
    """RAG 检索工具
    
    为 Agent 提供知识库检索和问答能力，支持：
    - 混合检索（向量 + 关键词）
    - 生成式回答
    - 来源引用
    - 置信度评分
    """
    
    name = "rag_search"
    description = """检索知识库中的相关文档，并基于检索结果生成回答。

使用场景：
- 回答关于文档内容的问题
- 查找特定信息
- 总结文档要点

参数说明：
- query: 用户的问题或查询（必需）
- top_k: 返回的相关文档数量，默认 5，范围 1-20
- filters: 可选的过滤条件，支持 category_id, tags, date_range

返回内容包括：
- answer: 基于检索结果生成的回答
- sources: 引用的来源文档列表（含文档ID、标题、相关度）
- confidence: 回答的置信度（0-1）
"""
    
    def __init__(
        self,
        rag_engine: RAGEngine,
        search_service: Optional[SearchService] = None
    ):
        self.rag_engine = rag_engine
        self.search_service = search_service
        logger.info("RAGTool initialized")
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """获取参数 Schema"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "用户的问题或查询语句"
                },
                "top_k": {
                    "type": "integer",
                    "description": "返回的相关文档数量",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20
                },
                "filters": {
                    "type": "object",
                    "description": "可选的过滤条件",
                    "properties": {
                        "category_id": {
                            "type": "string",
                            "description": "按分类过滤"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "按标签过滤"
                        },
                        "date_from": {
                            "type": "string",
                            "description": "起始日期 (ISO8601)"
                        },
                        "date_to": {
                            "type": "string",
                            "description": "结束日期 (ISO8601)"
                        }
                    }
                }
            },
            "required": ["query"]
        }
    
    async def execute(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """执行 RAG 检索
        
        Args:
            query: 用户查询
            top_k: 返回文档数量
            filters: 过滤条件
            
        Returns:
            包含回答、来源、置信度的字典
        """
        try:
            logger.info(f"RAG search: query='{query[:50]}...', top_k={top_k}")
            
            # 构建 RAG 查询
            rag_query = RAGQuery(
                query=query,
                top_k=top_k,
                search_mode=SearchMode.HYBRID,
                filters=filters or {},
                generate_answer=True,
                include_sources=True
            )
            
            # 执行检索
            result = await self.rag_engine.query(rag_query)
            
            # 格式化来源
            sources = []
            for src in result.sources:
                source = {
                    "document_id": src.document_id,
                    "document_title": src.document_title,
                    "chunk_index": src.chunk_index,
                    "content_preview": (
                        src.content[:200] + "..." 
                        if len(src.content) > 200 
                        else src.content
                    ),
                    "relevance_score": round(src.relevance_score, 4)
                }
                sources.append(source)
            
            # 返回结果
            return {
                "success": True,
                "query": query,
                "answer": result.answer,
                "sources": sources,
                "confidence": round(result.confidence, 4),
                "total_chunks": len(result.sources),
                "retrieval_time_ms": result.retrieval_time_ms
            }
            
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "answer": None,
                "sources": [],
                "confidence": 0.0
            }


class SearchTool(BaseTool):
    """文档搜索工具
    
    简单的文档搜索，返回文档列表而不生成回答。
    适用于需要浏览文档的场景。
    """
    
    name = "search_documents"
    description = """搜索知识库中的文档，返回匹配的文档列表。

使用场景：
- 查找特定文档
- 浏览相关文档
- 获取文档元数据

参数说明：
- query: 搜索关键词
- limit: 返回文档数量，默认 10
- filters: 可选的过滤条件
"""
    
    def __init__(self, search_service: SearchService):
        self.search_service = search_service
        logger.info("SearchTool initialized")
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回文档数量",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50
                },
                "filters": {
                    "type": "object",
                    "description": "过滤条件"
                }
            },
            "required": ["query"]
        }
    
    async def execute(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """执行文档搜索"""
        try:
            search_query = SearchQuery(
                query=query,
                limit=limit,
                search_mode="hybrid",
                filters=filters or {}
            )
            
            results = await self.search_service.search(search_query)
            
            return {
                "success": True,
                "query": query,
                "total": len(results),
                "documents": [
                    {
                        "id": doc.id,
                        "title": doc.title,
                        "category": doc.category_name,
                        "score": round(doc.score, 4) if hasattr(doc, 'score') else None
                    }
                    for doc in results
                ]
            }
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "documents": []
            }


class DocumentTool(BaseTool):
    """文档详情工具
    
    获取特定文档的详细内容。
    """
    
    name = "get_document"
    description = """获取指定文档的详细内容。

参数：
- document_id: 文档ID（必需）
"""
    
    def __init__(self, search_service: SearchService):
        self.search_service = search_service
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "string",
                    "description": "文档ID"
                }
            },
            "required": ["document_id"]
        }
    
    async def execute(
        self,
        document_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """获取文档详情"""
        try:
            doc = await self.search_service.get_document(document_id)
            if not doc:
                return {
                    "success": False,
                    "error": f"Document not found: {document_id}"
                }
            
            return {
                "success": True,
                "document": {
                    "id": doc.id,
                    "title": doc.title,
                    "content": doc.content[:5000] if hasattr(doc, 'content') else None,
                    "metadata": doc.metadata if hasattr(doc, 'metadata') else {}
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def register_rag_tools(
    agent_registry,
    rag_engine: RAGEngine,
    search_service: SearchService
) -> None:
    """向 Agent 注册 RAG 相关工具
    
    Args:
        agent_registry: Agent 工具注册表
        rag_engine: RAG 引擎实例
        search_service: 搜索服务实例
    """
    # 注册 RAG 检索工具
    rag_tool = RAGTool(rag_engine, search_service)
    agent_registry.register(rag_tool)
    
    # 注册搜索工具
    search_tool = SearchTool(search_service)
    agent_registry.register(search_tool)
    
    # 注册文档工具
    doc_tool = DocumentTool(search_service)
    agent_registry.register(doc_tool)
    
    logger.info("RAG tools registered to agent")
