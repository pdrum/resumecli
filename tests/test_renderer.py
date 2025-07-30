import os
from dataclasses import dataclass
from typing import Any, Dict, List, cast

import pytest
import yaml
from bs4 import BeautifulSoup, Tag

from src.renderer import ResumeRenderer, ResumeTemplate


@dataclass
class CandidateParentElement:
    element: Tag
    distance: int

    def __lt__(self, other: "CandidateParentElement") -> bool:
        return self.distance < other.distance


def load_sample_cv() -> Dict[str, Any]:
    sample_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cv.sample.yaml")
    with open(sample_path, "r") as f:
        sample_yaml = f.readlines()[1:]
        return cast(Dict[str, Any], yaml.safe_load("".join(sample_yaml)))


def assert_each_list_belong_to_distinct_section(soup: BeautifulSoup, *string_lists: List[str]) -> None:
    found_elements = [find_closest_parent_containing_all(soup, strings) for strings in string_lists]
    assert_elements_are_distinct(found_elements)


def find_closest_parent_containing_all(soup: BeautifulSoup, strings: List[str]) -> Tag:
    candidates = find_candidate_parent_elements(soup, strings)

    if not candidates:
        assert False, f"Could not find an HTML element containing all strings in {strings}"

    return min(candidates).element


def find_elements_containing_any_of(soup: BeautifulSoup, strings: List[str]) -> List[Tag]:
    individual_elements = []
    for s in strings:
        elements = [elem for elem in soup.find_all(string=lambda text: s in text if text else False)]
        if elements:
            individual_elements.extend(elements)
    return individual_elements


def find_strings_to_look_for_position(position_data: Dict[str, Any]) -> List[str]:
    description = position_data.get("description")
    description_lines = description.splitlines() if description else []
    description_look_up_strings = [line.strip("* ") for line in description_lines if line.strip()]
    result = (
        [
            position_data.get("title", ""),
            position_data.get("startDate", ""),
            position_data.get("endDate", "") or "Present",
        ]
        + description_look_up_strings
        + position_data.get("skills", [])
    )
    return cast(List[str], result)


def find_candidate_parent_elements(soup: BeautifulSoup, strings: List[str]) -> List[CandidateParentElement]:
    elements = find_elements_containing_any_of(soup, strings)
    candidates = []

    for element in elements:
        current = element
        distance = 0
        while current and current.name != "body":
            parent_text = current.get_text()
            if all(s in parent_text for s in strings):
                candidates.append(CandidateParentElement(element=current, distance=distance))
                break

            current = current.parent
            distance += 1

    return candidates


def assert_elements_are_distinct(elements: List[Tag]) -> None:
    for i in range(len(elements)):
        for j in range(i + 1, len(elements)):
            assert elements[i] != elements[j], (
                f"Found the same HTML element for string lists {i+1} and {j+1}.\n"
                f"Lists should be in distinct sections but both are in: {elements[i]}"
            )


class TestRenderer:
    @pytest.fixture
    def renderer(self) -> ResumeRenderer:
        return ResumeRenderer()

    @pytest.mark.parametrize("template", list(ResumeTemplate))
    def test_position_rendering(self, renderer: ResumeRenderer, template: ResumeTemplate) -> None:
        cv_data = load_sample_cv()

        all_positions = []
        for experience_item in cv_data["experience"]:
            all_positions.extend(experience_item["positions"])

        expected_string_list_for_each_position = [
            find_strings_to_look_for_position(position_data) for position_data in all_positions
        ]

        rendered_html = renderer.render_resume(cv_data, template)
        soup = BeautifulSoup(rendered_html, "html.parser")
        assert_each_list_belong_to_distinct_section(soup, *expected_string_list_for_each_position)

    @pytest.mark.parametrize("template", list(ResumeTemplate))
    def test_experience_rendering(self, renderer: ResumeRenderer, template: ResumeTemplate) -> None:
        cv_data = load_sample_cv()
        experiences = cv_data.get("experience", [])

        expected_string_list_for_each_experience = [
            [e.get("company", ""), e.get("description", "")] for e in experiences
        ]

        rendered_html = renderer.render_resume(cv_data, template)
        soup = BeautifulSoup(rendered_html, "html.parser")
        assert_each_list_belong_to_distinct_section(soup, *expected_string_list_for_each_experience)

    @pytest.mark.parametrize("template", list(ResumeTemplate))
    def test_education_rendering(self, renderer: ResumeRenderer, template: ResumeTemplate) -> None:
        cv_data = load_sample_cv()
        educations = cv_data["education"]

        expected_string_list_for_each_education = [
            [e["school"], e["degree"], e["startDate"], e.get("endDate", "")] for e in educations
        ]

        rendered_html = renderer.render_resume(cv_data, template)
        soup = BeautifulSoup(rendered_html, "html.parser")
        assert_each_list_belong_to_distinct_section(soup, *expected_string_list_for_each_education)

    @pytest.mark.parametrize("template", list(ResumeTemplate))
    def test_language_rendering(self, renderer: ResumeRenderer, template: ResumeTemplate) -> None:
        cv_data = load_sample_cv()
        languages = cv_data["languages"]

        expected_string_list_for_each_language = [[lang["language"], lang["level"]] for lang in languages]

        rendered_html = renderer.render_resume(cv_data, template)
        soup = BeautifulSoup(rendered_html, "html.parser")

        assert_each_list_belong_to_distinct_section(soup, *expected_string_list_for_each_language)

    @pytest.mark.parametrize("template", list(ResumeTemplate))
    def test_contact_rendering(self, renderer: ResumeRenderer, template: ResumeTemplate) -> None:
        cv_data = load_sample_cv()
        contact = cv_data["contact"]

        expected_strings = [
            contact["email"],
            contact["phone"],
            contact["github"],
            contact["blog"],
            contact["linkedin"],
        ] + contact["links"]

        rendered_html = renderer.render_resume(cv_data, template)
        soup = BeautifulSoup(rendered_html, "html.parser")

        assert (
            find_closest_parent_containing_all(soup, expected_strings) is not None
        ), "Could not find an HTML element containing all contact information strings."

    def test_render_error(self, renderer: ResumeRenderer) -> None:
        error_message = "Test error message"
        rendered_html = renderer.render_error(error_message)

        soup = BeautifulSoup(rendered_html, "html.parser")

        assert error_message in soup.get_text(), "Error message not found in rendered HTML"
