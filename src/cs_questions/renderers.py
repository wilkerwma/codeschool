from iospec.feedback import Feedback
from codeschool.shortcuts import render_html


render_html.register_template(Feedback, 'render/feedback.jinja2')
