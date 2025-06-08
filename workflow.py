from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from activities import AgentParams, run_agent


@workflow.defn
class LangChainWorkflow:
    @workflow.run
    async def run(self, params: AgentParams) -> dict:
        return await workflow.execute_activity(
            run_agent,
            params,
            schedule_to_close_timeout=timedelta(seconds=180),
        )


@workflow.defn
class LoaderWorkFlow:
    @workflow.run
    async def run(self, params: AgentParams) -> dict:
        agent_answer = await workflow.execute_child_workflow(
            LangChainWorkflow.run,
            params,
            id="child-summary",
        )
        page_content = agent_answer.get("messages")[-1].get("content")
        store_params = {
            "agent": "store_document",
            "payload": {"page_content": page_content},
        }
        await workflow.execute_child_workflow(
            LangChainWorkflow.run,
            AgentParams(**store_params),
            id="child-summary-store",
        )
        return agent_answer.get("messages")[-1]
