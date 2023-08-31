from datetime import datetime, timedelta, timezone
from re import compile as re_compile

from statics import Rating, RatingSVG

readme_replace_regex = re_compile(r"<!-- BEGIN INPUT -->[\s\S]*<!-- END INPUT -->")

img_relative_path_in_reviews = "![](../../images/{})"
img_relative_path_in_root = "![](./images/{})"
img_path_with_size = (
    '<img src="https://github.com/GLGDLY/HKUST_courses_space/raw/master/images/{}" '
    'width="{}" height="{}">'
)


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

    def render(self, title: str, author: str, issue_id: str) -> str:
        """
        render the review on review_template.md
        :param title: title of the review
        :param author: author of the review
        :return: markdown string
        """
        d = self.data.copy()
        d["Date"] = datetime.now(tz=timezone(offset=timedelta(hours=8))).strftime(
            "%Y-%m-%d %H:%M on HK Time"
        )
        d["Author"] = author
        d["Contents"] = (
            "| "
            + " | ".join(d["Contents"])
            + " |\n"
            + "|"
            + (len(d["Contents"]) * " ---------------- |")
        )
        d["Rating for Content"] = img_path_with_size.format(
            RatingSVG[d["Rating for Content"]], 30, 30
        )
        d["Rating for Teaching"] = img_path_with_size.format(
            RatingSVG[d["Rating for Teaching"]], 30, 30
        )
        d["Rating for Grade"] = img_path_with_size.format(
            RatingSVG[d["Rating for Grade"]], 30, 30
        )
        d["Rating for Workload"] = img_path_with_size.format(
            RatingSVG[d["Rating for Workload"]], 30, 30
        )
        d["Rating Overall"] = img_path_with_size.format(
            RatingSVG[d["Rating Overall"]], 40, 40
        )

        d["ISSUE ID"] = issue_id

        with open("./reviews/review_template.md", "r") as f:
            template = f.read()
        return template.format(title=title, **d)

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
        course_content += "| Course | Intro | Rating |\n"
        course_content += "| --------- | --------- | --------- |\n"
        for course in all_courses:
            course_content += "| [{}]({}) | {} | {} |\n".format(
                course,
                "./reviews/" + course,
                all_courses[course]["intro"],
                img_relative_path_in_root.format(
                    RatingSVG[
                        round(
                            sum(all_courses[course]["overall_rating_sum"].values())
                            / len(all_courses[course]["overall_rating_sum"])
                        )
                    ]
                ),
            )
        course_content += "\n\n<!-- END INPUT -->"

        self.readme = readme_replace_regex.sub(course_content, self.readme)
        with open("./README.md", "w") as f:
            f.write(self.readme)


class CourseReadmeIO:
    def __init__(self, course_code: str, course_intro: str):
        with open("./reviews/review_readme_template.md", "r") as template:
            self.readme = template.read().format(Course=course_code, Intro=course_intro)
        with open("./reviews/" + course_code + "/README.md", "w") as f:
            f.write(self.readme)

    def write(self, course: dict, course_code: str):
        # calculate course average rating and save as svg for course->README.md
        content_avg_rating = img_path_with_size.format(
            RatingSVG[
                round(
                    sum(course["content_rating_sum"].values())
                    / len(course["content_rating_sum"])
                )
            ],
            30,
            30,
        )
        teaching_avg_rating = img_path_with_size.format(
            RatingSVG[
                round(
                    sum(course["teaching_rating_sum"].values())
                    / len(course["teaching_rating_sum"])
                )
            ],
            30,
            30,
        )
        grade_avg_rating = img_path_with_size.format(
            RatingSVG[
                round(
                    sum(course["grade_rating_sum"].values())
                    / len(course["grade_rating_sum"])
                )
            ],
            30,
            30,
        )
        workload_avg_rating = img_path_with_size.format(
            RatingSVG[
                round(
                    sum(course["workload_rating_sum"].values())
                    / len(course["workload_rating_sum"])
                )
            ],
            30,
            30,
        )
        overall_avg_rating = img_path_with_size.format(
            RatingSVG[
                round(
                    sum(course["overall_rating_sum"].values())
                    / len(course["overall_rating_sum"])
                )
            ],
            50,
            50,
        )

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
        course_content += "***Overall Rating:***\n\n{}\n\n".format(overall_avg_rating)
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
