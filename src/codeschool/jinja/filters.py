from djinga.register import jj_filter, jj_global


#@jj_filter
def markdown(text, *args, **kwargs):
    from markdown import markdown
    return markdown(text, *args, **kwargs)
