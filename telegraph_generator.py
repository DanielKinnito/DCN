from telegraph import Telegraph
from database import get_news_for_user

telegraph = Telegraph()
telegraph.create_account(short_name='NewsAggregatorBot')

def create_telegraph_page(channel_name, text, image_url):
    content = f'<p>{text}</p>'
    if image_url:
        content = f'<img src="{image_url}">' + content

    response = telegraph.create_page(
        title=f'News from {channel_name}',
        html_content=content
    )
    return 'https://telegra.ph/{}'.format(response['path'])