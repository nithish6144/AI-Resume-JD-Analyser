import os
import json

from pypdf import PdfReader
from dotenv import load_dotenv
from groq import Groq


load_dotenv()


def extract_resume_text(pdf_file):

    try:

        reader = PdfReader(pdf_file)

        text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:

                text += page_text + "\n"


        if not text.strip():

            raise ValueError(
                "No readable text was found in the PDF."
            )


        return text.strip()


    except ValueError:

        raise


    except Exception as exc:

        raise ValueError(
            "Unable to read the PDF resume."
        ) from exc



def call_groq(prompt):

    api_key = os.getenv(
        "GROQ_API_KEY"
    )


    if not api_key:

        raise ValueError(
            "GROQ_API_KEY is missing from the .env file."
        )


    try:

        client = Groq(
            api_key=api_key
        )


        response = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[

                {
                    "role": "system",
                    "content":
                    (
                        "You are an expert ATS resume "
                        "analysis assistant. Always return "
                        "only valid JSON."
                    )
                },

                {
                    "role": "user",
                    "content": prompt
                }

            ],

            response_format={
                "type": "json_object"
            },

            temperature=0.2

        )


        raw_response = (

            response
            .choices[0]
            .message
            .content

        )


        if not raw_response:

            raise ValueError(
                "AI returned an empty response."
            )


        return json.loads(
            raw_response
        )


    except json.JSONDecodeError as exc:

        raise ValueError(
            "AI returned an invalid JSON response."
        ) from exc


    except ValueError:

        raise


    except Exception as exc:

        print(
            "\n========== GROQ API ERROR =========="
        )

        print(
            type(exc).__name__
        )

        print(
            str(exc)
        )

        print(
            "====================================\n"
        )


        raise ValueError(
            "AI analysis is temporarily unavailable. "
            "Please try again."
        ) from exc



def match_resume_with_jd(
    resume_text,
    job_description
):

    prompt = f"""
Compare the following resume with the job description.

Analyse technical skills, tools, frameworks,
platforms, and relevant job requirements.

MATCH SCORE RULES:

- 90 to 100: Excellent alignment.
- 75 to 89: Strong alignment.
- 60 to 74: Moderate alignment.
- 40 to 59: Weak alignment.
- 0 to 39: Poor alignment.

Do not inflate the match score.

A skill is matched only when the resume clearly
supports that skill.

A missing skill must be relevant to the provided
job description.

Provide exactly 3 actionable resume suggestions.

Return ONLY valid JSON.

Do not use markdown.
Do not use code blocks.
Do not include text before or after the JSON.

Use exactly this JSON structure:

{{
    "match_score": 0,
    "matched_skills": [
        "skill"
    ],
    "missing_skills": [
        "skill"
    ],
    "suggestions": [
        "suggestion 1",
        "suggestion 2",
        "suggestion 3"
    ]
}}

RESUME:

{resume_text}


JOB DESCRIPTION:

{job_description}
"""


    result = call_groq(
        prompt
    )


    required_fields = {

        "match_score",
        "matched_skills",
        "missing_skills",
        "suggestions"

    }


    if not isinstance(
        result,
        dict
    ):

        raise ValueError(
            "Invalid AI response."
        )


    if not required_fields.issubset(
        result.keys()
    ):

        raise ValueError(
            "AI response is missing required fields."
        )


    if not isinstance(
        result["match_score"],
        int
    ):

        raise ValueError(
            "Invalid match score."
        )


    result["match_score"] = max(

        0,

        min(
            result["match_score"],
            100
        )

    )


    if not isinstance(
        result["matched_skills"],
        list
    ):

        raise ValueError(
            "Matched skills must be an array."
        )


    if not isinstance(
        result["missing_skills"],
        list
    ):

        raise ValueError(
            "Missing skills must be an array."
        )


    if not isinstance(
        result["suggestions"],
        list
    ):

        raise ValueError(
            "Suggestions must be an array."
        )


    return result



def improve_resume(
    resume_text,
    job_description,
    match_result
):

    matched_skills = match_result.get(
        "matched_skills",
        []
    )


    missing_skills = match_result.get(
        "missing_skills",
        []
    )


    prompt = f"""
You are an expert ATS resume writer and
technical recruiter.

Improve the candidate's resume for the provided
job description.

IMPORTANT RULES:

- Never invent experience.
- Never invent projects.
- Never invent technologies.
- Never claim the candidate used a missing skill.
- Never create fake certifications.
- Never invent job responsibilities.
- Never invent numerical metrics.
- Never invent percentages.
- Never invent revenue impact.
- Never invent team sizes.

Only rewrite information clearly supported by
the resume.

Identify weak or generic resume bullets.

Rewrite them using:

- Strong action verbs.
- Clear technical contributions.
- Technologies already present in the resume.
- Relevant ATS keywords.
- Concise professional language.

Create between 3 and 5 bullet improvements.

Recommend keywords only when the candidate's
existing experience reasonably supports them.

Provide one concise final resume strategy.

Return ONLY valid JSON.

Do not use markdown.
Do not use code blocks.
Do not include text before or after the JSON.

Use exactly this JSON structure:

{{
    "improved_bullets": [
        {{
            "original": "Original resume bullet",
            "improved": "Improved resume bullet"
        }}
    ],
    "keywords_to_consider": [
        "keyword"
    ],
    "final_strategy": "Resume positioning strategy"
}}

RESUME:

{resume_text}


JOB DESCRIPTION:

{job_description}


MATCHED SKILLS:

{matched_skills}


MISSING SKILLS:

{missing_skills}
"""


    result = call_groq(
        prompt
    )


    required_fields = {

        "improved_bullets",
        "keywords_to_consider",
        "final_strategy"

    }


    if not isinstance(
        result,
        dict
    ):

        raise ValueError(
            "Invalid optimization response."
        )


    if not required_fields.issubset(
        result.keys()
    ):

        raise ValueError(
            "Optimization response is missing fields."
        )


    if not isinstance(
        result["improved_bullets"],
        list
    ):

        raise ValueError(
            "Improved bullets must be an array."
        )


    if not isinstance(
        result["keywords_to_consider"],
        list
    ):

        raise ValueError(
            "Keywords must be an array."
        )


    if not isinstance(
        result["final_strategy"],
        str
    ):

        raise ValueError(
            "Final strategy must be text."
        )


    return result