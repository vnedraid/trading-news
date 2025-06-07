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
