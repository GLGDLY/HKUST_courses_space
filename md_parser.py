import os
from datetime import datetime
from re import compile as re_compile

from statics import Rating, RatingSVG

readme_replace_regex = re_compile(r"<!-- BEGIN INPUT -->[\s\S]*<!-- END INPUT -->")


class ReviewParser:
    """
    parse review issue body
    """

    def __init__(self, md: str):
        self.data = {}
        self.__parse(md)
        for item in self.data:
            self.data[item] = self.data[item].strip()
        self.data["Course Code"] = self.data["Course Code"].replace(" ", "").upper()
        self.data["Contents"] = self.data["Contents"].splitlines()
        self.data["Rating for Content"] = getattr(
            Rating, self.data["Rating for Content"], Rating.A
        ).value
        self.data["Rating for Teaching"] = getattr(
            Rating, self.data["Rating for Teaching"], Rating.A
        ).value
        self.data["Rating for Grade"] = getattr(
            Rating, self.data["Rating for Grade"], Rating.A
        ).value
        self.data["Rating for Workload"] = getattr(
            Rating, self.data["Rating for Workload"], Rating.A
        ).value
        self.data["Rating Overall"] = (
            self.data["Rating for Content"]
            + self.data["Rating for Teaching"]
            + self.data["Rating for Grade"]
            + self.data["Rating for Workload"]
        ) // 4

    def __parse(self, md: str):
        current_section = None
        for line in md.splitlines():
            if line.startswith("### "):
                current_section = line[4:].strip()
                self.data[current_section] = ""
            elif current_section == "Contents":
                if line.startswith("- [X]"):
                    self.data[current_section] += line[5:].strip() + "\n"
            elif current_section is not None and line and not line.startswith("```"):
                self.data[current_section] += line + "\n"

    def render(self, title: str, author: str) -> str:
        """
        render the review on review_template.md
        :param title: title of the review
        :param author: author of the review
        :return: markdown string
        """
        d = self.data.copy()
        d["Date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        d["Author"] = author
        d["Contents"] = (
            "| "
            + " | ".join(d["Contents"])
            + " |\n"
            + "|"
            + (len(d["Contents"]) * " ---------------- |")
        )
        d["Rating for Content"] = RatingSVG[d["Rating for Content"]]
        d["Rating for Teaching"] = RatingSVG[d["Rating for Teaching"]]
        d["Rating for Grade"] = RatingSVG[d["Rating for Grade"]]
        d["Rating for Workload"] = RatingSVG[d["Rating for Workload"]]
        d["Rating Overall"] = RatingSVG[d["Rating Overall"]]

        with open("./reviews/review_template.md", "r") as f:
            template = f.read()
        return template.format(title=title, **self.data)

    @property
    def course_code(self) -> str:
        return self.data["Course Code"]

    @property
    def rating_content(self) -> int:
        return self.data["Rating for Content"]

    @property
    def rating_teaching(self) -> int:
        return self.data["Rating for Teaching"]

    @property
    def rating_grade(self) -> int:
        return self.data["Rating for Grade"]

    @property
    def rating_workload(self) -> int:
        return self.data["Rating for Workload"]

    @property
    def rating_overall(self) -> int:
        return self.data["Rating Overall"]


class ReadmeIO:
    def __init__(self):
        with open("./README.md", "r") as f:
            self.readme = f.read()

    def write(self, all_courses: dict):
        course_content = "<!-- BEGIN INPUT -->\n"
        for course in all_courses:
            course_content += "- [{} - {} ({})]({})\n".format(
                course,
                all_courses[course]["intro"],
                Rating(
                    round(
                        all_courses[course]["overall_rating_sum"]
                        / all_courses[course]["rating_number"]
                    )
                ).name,
                "./reviews/" + course,
            )
        course_content += "<!-- END INPUT -->"

        self.readme = readme_replace_regex.sub(course_content, self.readme)
        with open("./README.md", "w") as f:
            f.write(self.readme)


class CourseReadmeIO:
    def __init__(self, course_code: str, course_intro: str):
        if not os.path.exists("./reviews/" + course_code + "/README.md"):
            with open("./reviews/" + course_code + "/README.md", "w") as f:
                with open("./course_readme_template.md", "r") as template:
                    f.write(template.read().format(Course=course_code + " - " + course_intro))
        else:
            with open("./reviews/" + course_code + "/README.md", "r") as f:
                self.readme = f.read()

    def write(self, course: dict, course_code: str):
        # calculate course average rating and save as svg for course->README.md
        content_avg_rating = RatingSVG[
            round(course["content_rating_sum"] / course["rating_number"])
        ]
        teaching_avg_rating = RatingSVG[
            round(course["teaching_rating_sum"] / course["rating_number"])
        ]
        grade_avg_rating = RatingSVG[
            round(course["grade_rating_sum"] / course["rating_number"])
        ]
        workload_avg_rating = RatingSVG[
            round(course["workload_rating_sum"] / course["rating_number"])
        ]
        overall_avg_rating = RatingSVG[
            round(course["overall_rating_sum"] / course["rating_number"])
        ]

        # construct content
        course_content = "<!-- BEGIN INPUT -->\n\n"
        course_content += "## Summary\n\n"
        course_content += "| Content | Teaching | Grade | Workload |\n"
        course_content += "| --------- | --------- | --------- | --------- |\n"
        course_content += "| {} | {} | {} | {} |\n\n".format(
            content_avg_rating,
            teaching_avg_rating,
            grade_avg_rating,
            workload_avg_rating,
        )
        course_content += "***Overall Rating: {}***\n\n".format(overall_avg_rating)
        course_content += "## Reviews\n\n"
        for issue_id in course["reviews"]:
            course_content += "- [{}]({})\n".format(
                course["reviews"][issue_id], f"{issue_id}.md"
            )
        course_content += "\n<!-- END INPUT -->"

        # write to file
        self.readme = readme_replace_regex.sub(course_content, self.readme)
        with open("./reviews/" + course_code + "/README.md", "w") as f:
            f.write(self.readme)
