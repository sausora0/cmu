from django import template
from teachers.models import StudentAnswer  # adjust if your model name is different

register = template.Library()

@register.filter
def get_answer(question, user):
    """
    Returns the student's answer for a given question if it exists.
    Usage in template: {{ question|get_answer:user }}
    """
    try:
        answer = StudentAnswer.objects.get(question=question, student=user)
        return answer.answer_text if answer.answer_text else answer.option.text
    except StudentAnswer.DoesNotExist:
        return ""
