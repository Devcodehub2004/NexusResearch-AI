import sys
from agents import (
    build_reader_agent,
    build_search_agent,
    writer_chain,
    critic_chain,
)
from history import save_research

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")



def run_research_pipeline(topic: str) -> dict:
    state = {}

    # ============================================================
    # STEP 1 - SEARCH AGENT
    # ============================================================

    print("\n" + "=" * 50)
    print("STEP 1 - Search agent is working...")
    print("=" * 50)

    search_agent = build_search_agent()

    search_result = search_agent.invoke({
        "messages": [
            (
                "user",
                f"Find recent, reliable and detailed information about: {topic}"
            )
        ]
    })

    state["search_results"] = search_result["messages"][-1].content

    print("\nSearch Result:\n")
    print(state["search_results"])

    # ============================================================
    # STEP 2 - READER AGENT
    # ============================================================

    print("\n" + "=" * 50)
    print("STEP 2 - Reader agent is scraping top resources...")
    print("=" * 50)

    reader_agent = build_reader_agent()

    reader_result = reader_agent.invoke({
        "messages": [
            (
                "user",
                f"""
Based on the following search results about '{topic}',
pick the single most relevant URL and scrape it for deeper content.

Search Results:
{state["search_results"][:3000]}
"""
            )
        ]
    })

    state["scraped_content"] = reader_result["messages"][-1].content

    print("\nScraped Content:\n")
    print(state["scraped_content"])

    # ============================================================
    # STEP 3 - WRITER
    # ============================================================

    print("\n" + "=" * 50)
    print("STEP 3 - Writer is drafting the report...")
    print("=" * 50)

    research_combined = (
        f"SEARCH RESULTS:\n"
        f"{state['search_results']}\n\n"
        f"DETAILED SCRAPED CONTENT:\n"
        f"{state['scraped_content']}"
    )

    state["report"] = writer_chain.invoke({
        "topic": topic,
        "research": research_combined,
    })

    print("\nFinal Report:\n")
    print(state["report"])

    # ============================================================
    # STEP 4 - CRITIC
    # ============================================================

    print("\n" + "=" * 50)
    print("STEP 4 - Critic is reviewing the report...")
    print("=" * 50)

    state["feedback"] = critic_chain.invoke({
        "report": state["report"],
    })

    print("\nCritic Report:\n")
    print(state["feedback"])

    # ── Save to history ──
    save_research(topic, state)
    print("\n💾 Research saved to history!")

    return state


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    topic = input("\nEnter a research topic: ")

    run_research_pipeline(topic)