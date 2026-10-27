"""Web search helper for ExamPass — provides search query templates."""

# Search query templates for optimizing the analysis prompts
KNOWLEDGE_PROMPT_QUERIES = [
    "how to create effective study guides from lecture slides AI prompt",
    "best practices for extracting exam key points from course materials",
    "knowledge distillation from PowerPoint to study notes prompt engineering",
]

TEST_QUERIES = [
    "how to generate effective practice test questions from study materials AI",
    "spaced repetition test question design best practices",
    "Bloom's taxonomy test question generation prompt",
]

EXAM_QUERIES = [
    "university final exam question design principles",
    "how to create comprehensive final exam blueprint",
    "college course final exam question types distribution",
]


def build_reference_search_queries(course_name: str) -> list:
    """Build search queries for finding reference exams from 211/985 universities."""
    return [
        f"211 985 {course_name} 期末考试试题",
        f"{course_name} 大学期末考试试卷及答案",
        f"{course_name} final exam questions and answers university",
        f"top university {course_name} examination paper sample",
        f"名校 {course_name} 期末考试真题",
    ]


def summarize_web_results(search_summary: str) -> str:
    """Format web search results into a readable reference section."""
    return f"""
## 网络调研参考

以下是从网络上搜集的类似课程考试信息，供出题时参考：

{search_summary}

请综合以上信息，设计出符合标准的试卷。
"""
