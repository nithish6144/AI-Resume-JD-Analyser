import os

from flask import Flask, render_template, request, session
from flask_session import Session
from dotenv import load_dotenv

from matcher import (
    extract_resume_text,
    match_resume_with_jd,
    improve_resume
)


load_dotenv()


app = Flask(__name__)


app.config["SECRET_KEY"] = os.getenv(
    "FLASK_SECRET_KEY",
    "development-secret-key"
)


app.config["MAX_CONTENT_LENGTH"] = (
    5 * 1024 * 1024
)


# SERVER-SIDE SESSION CONFIGURATION

app.config["SESSION_TYPE"] = "filesystem"

app.config["SESSION_FILE_DIR"] = os.path.join(
    app.root_path,
    "flask_session"
)

app.config["SESSION_PERMANENT"] = False

app.config["SESSION_USE_SIGNER"] = True


Session(app)


@app.route(
    "/",
    methods=["GET", "POST"]
)
def index():

    result = None
    optimization = None
    error = None


    if request.method == "POST":

        try:

            resume_file = request.files.get(
                "resume"
            )

            job_description = request.form.get(
                "job_description",
                ""
            ).strip()


            if (
                not resume_file
                or resume_file.filename == ""
            ):

                raise ValueError(
                    "Please upload your resume PDF."
                )


            if not resume_file.filename.lower().endswith(
                ".pdf"
            ):

                raise ValueError(
                    "Only PDF resume files are supported."
                )


            if not job_description:

                raise ValueError(
                    "Please paste the job description."
                )


            resume_text = extract_resume_text(
                resume_file
            )


            if not resume_text.strip():

                raise ValueError(
                    "No readable text was found in the PDF. "
                    "Please upload a text-based resume PDF."
                )


            result = match_resume_with_jd(
                resume_text=resume_text,
                job_description=job_description
            )


            # CLEAR OLD SESSION DATA

            session.clear()


            # SAVE ANALYSIS DATA SERVER-SIDE

            session["resume_text"] = resume_text

            session["job_description"] = (
                job_description
            )

            session["match_result"] = result


            print(
                "\n========== SESSION SAVED =========="
            )

            print(
                "Resume text:",
                len(resume_text),
                "characters"
            )

            print(
                "Job description:",
                len(job_description),
                "characters"
            )

            print(
                "Match result saved:",
                bool(result)
            )

            print(
                "===================================\n"
            )


        except ValueError as exc:

            error = str(exc)


        except Exception:

            app.logger.exception(
                "Resume matching failed"
            )

            error = (
                "Something went wrong while analysing "
                "your resume. Please try again."
            )


    return render_template(
        "index.html",
        result=result,
        optimization=optimization,
        error=error
    )


@app.route(
    "/improve",
    methods=["POST"]
)
def improve():

    print(
        "\n========== IMPROVE REQUEST =========="
    )

    print(
        "Session keys:",
        list(session.keys())
    )

    print(
        "=====================================\n"
    )


    result = session.get(
        "match_result"
    )

    resume_text = session.get(
        "resume_text"
    )

    job_description = session.get(
        "job_description"
    )


    optimization = None
    error = None


    if not result:

        error = (
            "Match analysis was not found. "
            "Please analyse the resume again."
        )


    elif not resume_text:

        error = (
            "Resume data was not found. "
            "Please analyse the resume again."
        )


    elif not job_description:

        error = (
            "Job description was not found. "
            "Please analyse the resume again."
        )


    else:

        try:

            optimization = improve_resume(
                resume_text=resume_text,
                job_description=job_description,
                match_result=result
            )


        except ValueError as exc:

            error = str(exc)


        except Exception:

            app.logger.exception(
                "Resume optimization failed"
            )

            error = (
                "Something went wrong while improving "
                "your resume."
            )


    return render_template(
        "index.html",
        result=result,
        optimization=optimization,
        error=error
    )


@app.errorhandler(413)
def file_too_large(error):

    return render_template(
        "index.html",
        result=None,
        optimization=None,
        error=(
            "The uploaded file is too large. "
            "Maximum file size is 5 MB."
        )
    ), 413


if __name__ == "__main__":

    app.run(
        debug=True
    )