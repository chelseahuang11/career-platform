from dataclasses import dataclass


@dataclass
class Profile:
    id: int
    name: str
    title: str
    location: str
    email: str
    linkedin: str
    github: str


@dataclass
class Project:
    id: int
    title: str
    summary: str
    technologies: str
    link: str
