"""
Промпты для генератора персон.
==============================
Промпт намеренно «наивный» — такой, каким студент напишет с первой
попытки. Он не запрещает markdown, не задаёт формат жёстко, не
перечисляет допустимые значения. Именно из-за этого на семинаре
мы увидим, как результат «течёт», и поймём, зачем нужна схема.
"""

SYSTEM_PROMPT = """You generate synthetic buyer personas for Russian
e-commerce. Create a plausible person: provide name, age, city, monthly
income, occupation, how often they shop online, and their favorite product
category.

Return the response as JSON."""

USER_PROMPT = "Create one persona."
