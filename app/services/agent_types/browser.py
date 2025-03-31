import asyncio
import json
import logging
import uuid

from browser_use.agent.views import AgentHistoryList
from browser_use.browser.browser import BrowserConfig, Browser
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing_extensions import ClassVar, Type, Optional
from browser_use import Agent as BrowserAgent


class BrowserUseInput(BaseModel):
    """Input for WriteFileTool."""

    instruction: str = Field(..., description="The instruction to use browser")


class BrowserTool(BaseTool):
    def __init__(
        self,
        llm: BaseChatModel,
        headless: bool = True,
        cache_dir: str = "/tmp/browser_history/",
    ):
        super().__init__()
        self.name: ClassVar[str] = "browser"
        self.args_schema: Type[BaseModel] = BrowserUseInput
        self.description: ClassVar[str] = (
            "Use this tool to interact with web browsers. "
            "Input should be a natural language description of what you want to do with the browser, "
            "such as 'Go to google.com and search for browser-use', or 'Navigate to Reddit and find "
            "the top post about AI'."
        )

        self.logger = logging.getLogger(__name__)
        self.llm = llm
        browser_config = BrowserConfig(headless=headless)
        self.browser = Browser(config=browser_config)
        self.cache_dir = cache_dir
        self._agent: Optional[BrowserAgent] = None

    def get_result(self, result_content: str, generated_gif_path: str) -> dict:
        return {
            "result_content": result_content,
            "generated_gif_path": generated_gif_path,
        }

    def _run(self, instruction: str) -> str:
        return asyncio.run(self._arun(instruction))

    async def terminate(self):
        """Terminate the browser agent if it exists."""
        if self._agent and self._agent.browser:
            try:
                await self._agent.browser.close()
            except Exception as e:
                self.logger.error(f"Error terminating browser agent: {str(e)}")
        self._agent = None

    async def _arun(self, instruction: str):
        generated_gif_path = f"{self.cache_dir}/{uuid.uuid4()}.gif"
        self._agent = BrowserAgent(
            task=instruction,
            llm=self.llm,
            browser=self.browser,
            generate_gif=generated_gif_path,
        )

        try:
            result = await self._agent.run()
            if isinstance(result, AgentHistoryList):
                return json.dumps(
                    self.get_result(result.final_result(), generated_gif_path)
                )
            else:
                return json.dumps(self.get_result(result, generated_gif_path))
        except Exception as e:
            return f"Error executing browser task: {str(e)}"
        finally:
            await self.terminate()
