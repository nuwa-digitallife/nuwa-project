"""
Claude CLI LLM Adapter for TradingAgents-CN
使用 `claude -p` 命令行模式，无需 API Key，走订阅额度。

核心思路：
- bind_tools() 存储工具引用，不传给 claude CLI
- _generate() 预执行工具，注入数据到 prompt，然后调 claude -p
- 返回 tool_calls=[] 的 AIMessage，触发 analyst 节点"直接用 content"路径
"""

import os
import re
import subprocess
import inspect
from typing import Any, Dict, List, Optional, Iterator

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')


class ClaudeCLILLM(BaseChatModel):
    """
    通过 `claude -p` 订阅模式调用 Claude，无需 API Key。
    bound_tools 中的工具会在 _generate() 内部预执行，结果作为上下文注入 prompt。
    返回的 AIMessage.tool_calls 始终为空列表，触发 analyst 节点直接使用 content 路径。
    """

    model: str = "claude-sonnet-4-6"
    timeout: int = 300

    # 存储通过 bind_tools() 绑定的工具（不序列化到 Pydantic schema）
    bound_tools: List[Any] = Field(default_factory=list, exclude=True)

    class Config:
        arbitrary_types_allowed = True

    @property
    def _llm_type(self) -> str:
        return "claude-cli"

    def bind_tools(self, tools, **kwargs) -> "ClaudeCLILLM":
        """存储工具引用，返回新实例（保持不可变约定）。"""
        new = ClaudeCLILLM(model=self.model, timeout=self.timeout)
        new.bound_tools = list(tools)
        logger.info(f"🔧 [ClaudeCLI] bind_tools: {[getattr(t, 'name', str(t)) for t in tools]}")
        return new

    # ─────────────────────────────────────────────
    # 核心生成方法
    # ─────────────────────────────────────────────

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager=None,
        **kwargs,
    ) -> ChatResult:
        """
        1. 从 messages 提取 ticker / date
        2. 调用 bound_tools 获取数据
        3. 将数据注入 messages，调 claude -p
        4. 返回 tool_calls=[] 的 AIMessage
        """
        ticker, start_date, end_date = self._extract_params(messages)
        logger.info(f"🔧 [ClaudeCLI] 提取参数: ticker={ticker}, start={start_date}, end={end_date}")

        # 构建最终消息列表（先复制，再追加工具数据）
        augmented_messages = list(messages)

        if self.bound_tools:
            tool_data_parts = []
            for tool in self.bound_tools:
                tool_name = getattr(tool, 'name', getattr(tool, '__name__', str(tool)))
                try:
                    args = self._build_tool_args(tool, ticker, start_date, end_date)
                    logger.info(f"🔧 [ClaudeCLI] 调用工具 {tool_name}，参数: {args}")
                    if hasattr(tool, 'invoke'):
                        data = tool.invoke(args)
                    elif callable(tool):
                        data = tool(**args)
                    else:
                        raise TypeError(f"工具 {tool_name} 不可调用")
                    data_str = str(data) if not isinstance(data, str) else data
                    tool_data_parts.append(f"[工具: {tool_name}]\n{data_str}")
                    logger.info(f"✅ [ClaudeCLI] 工具 {tool_name} 返回 {len(data_str)} 字符")
                except Exception as e:
                    logger.warning(f"⚠️ [ClaudeCLI] 工具 {tool_name} 失败: {e}")
                    tool_data_parts.append(f"[工具: {tool_name}] 数据获取失败: {e}")

            if tool_data_parts:
                tool_context = "\n\n".join(tool_data_parts)
                augmented_messages.append(
                    HumanMessage(content=f"以下是工具获取的实时数据，请基于这些数据进行分析：\n\n{tool_context}")
                )

        # 格式化为文本 prompt
        prompt = self._fmt(augmented_messages)
        logger.info(f"🔧 [ClaudeCLI] 发送 prompt，长度: {len(prompt)} 字符")

        # 调 claude CLI
        output = self._call_claude(prompt)
        logger.info(f"✅ [ClaudeCLI] 收到回复，长度: {len(output)} 字符")

        return ChatResult(generations=[
            ChatGeneration(
                message=AIMessage(content=output, tool_calls=[])
            )
        ])

    # ─────────────────────────────────────────────
    # 工具参数提取
    # ─────────────────────────────────────────────

    def _extract_params(self, messages: List[BaseMessage]):
        """从 messages 中提取 ticker 和日期。"""
        full_text = ""
        for msg in messages:
            if isinstance(msg.content, str):
                full_text += msg.content + "\n"

        ticker = self._extract_ticker(full_text)
        date = self._extract_date(full_text)

        return ticker, date, date

    def _extract_ticker(self, text: str) -> str:
        """从文本中提取股票代码。"""
        patterns = [
            r'股票代码[：:]\s*([A-Z0-9.]+)',
            r'ticker[：:\s]+([A-Z0-9.]+)',
            r'symbol[：:\s]+([A-Z0-9.]+)',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return ""

    def _extract_date(self, text: str) -> str:
        """从文本中提取分析日期（YYYY-MM-DD）。"""
        patterns = [
            r'分析日期[：:]\s*(\d{4}-\d{2}-\d{2})',
            r'current_date[：:\s]+(\d{4}-\d{2}-\d{2})',
            r'trade_date[：:\s]+(\d{4}-\d{2}-\d{2})',
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                return m.group(1).strip()

        # fallback: 任意 YYYY-MM-DD
        m = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', text)
        if m:
            return m.group(1)
        return ""

    def _build_tool_args(self, tool, ticker: str, start_date: str, end_date: str) -> Dict:
        """根据工具的 args_schema 字段名，构建调用参数。"""
        field_mapping = {
            'ticker': ticker,
            'symbol': ticker,
            'stock_code': ticker,
            'code': ticker,
            'start_date': start_date,
            'end_date': end_date,
            'curr_date': end_date,
            'current_date': end_date,
            'date': end_date,
            'trade_date': end_date,
            'query_date': end_date,
        }

        # 尝试从 args_schema 获取字段列表
        try:
            schema = tool.args_schema.schema()
            props = schema.get('properties', {})
            args = {}
            for field_name in props:
                if field_name in field_mapping and field_mapping[field_name]:
                    args[field_name] = field_mapping[field_name]
            if args:
                return args
        except Exception:
            pass

        # fallback: 检查 invoke 方法的参数名（LangChain Tool）或函数本身（普通函数）
        for target in [getattr(tool, 'invoke', None), tool if callable(tool) else None]:
            if target is None:
                continue
            try:
                sig = inspect.signature(target)
                args = {}
                for param_name in sig.parameters:
                    if param_name in field_mapping and field_mapping[param_name]:
                        args[param_name] = field_mapping[param_name]
                if args:
                    return args
            except Exception:
                pass

        # 最终 fallback: 用 ticker + date
        return {"ticker": ticker, "start_date": start_date, "end_date": end_date}

    # ─────────────────────────────────────────────
    # Prompt 格式化 & CLI 调用
    # ─────────────────────────────────────────────

    def _fmt(self, messages: List[BaseMessage]) -> str:
        """将 LangChain messages 转换为纯文本 prompt。"""
        parts = []
        for msg in messages:
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            if isinstance(msg, SystemMessage):
                parts.append(f"[系统指令]\n{content}")
            elif isinstance(msg, HumanMessage):
                parts.append(f"[用户]\n{content}")
            elif isinstance(msg, AIMessage):
                parts.append(f"[助手]\n{content}")
            else:
                parts.append(content)
        return "\n\n".join(parts)

    def _call_claude(self, prompt: str) -> str:
        """通过 claude -p 调用 Claude CLI。"""
        try:
            # 去掉 CLAUDECODE 环境变量，允许在 Claude Code 会话内启动子进程
            env = os.environ.copy()
            env.pop("CLAUDECODE", None)
            result = subprocess.run(
                ["claude", "-p", prompt, "--model", self.model, "--output-format", "text"],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env,
            )
            if result.returncode != 0:
                err = result.stderr.strip()
                logger.error(f"❌ [ClaudeCLI] 进程返回非零: {result.returncode}, stderr: {err[:200]}")
                return f"[Claude CLI 错误 (code={result.returncode})]: {err}"
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.error(f"❌ [ClaudeCLI] 超时（{self.timeout}s）")
            return f"[Claude CLI 超时（{self.timeout}s）]"
        except FileNotFoundError:
            logger.error("❌ [ClaudeCLI] 找不到 claude 命令，请确认 Claude CLI 已安装")
            return "[错误：找不到 claude 命令，请安装 Claude CLI]"
        except Exception as e:
            logger.error(f"❌ [ClaudeCLI] 未知错误: {e}")
            return f"[Claude CLI 错误: {e}]"

    # ─────────────────────────────────────────────
    # LangChain 必须实现的接口
    # ─────────────────────────────────────────────

    def _stream(self, messages, stop=None, run_manager=None, **kwargs) -> Iterator[ChatGeneration]:
        result = self._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
        yield result.generations[0]

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model": self.model, "timeout": self.timeout}
