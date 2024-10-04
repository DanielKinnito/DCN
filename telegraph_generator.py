from telegraph import Telegraph
from database import get_news_for_user

telegraph = Telegraph()
telegraph.create_account(short_name='news_bot')

def generate_telegraph_view(user_id):
    news = get_news_for_user(user_id)
    
    content = ""
    for channel_name, headline, photo_url, post_link in news:
        content += f'<h3>{channel_name}</h3>'
        if photo_url:
            content += f'<img src="{photo_url}">'
        content += f'<p>{headline}</p>'
        content += f'<a href="{post_link}">Read more</a><br><br>'
    
    title = "Your Personalized News Feed"
    author_name = "News Bot"
    
    response = telegraph.create_page(title, html_content=content, author_name=author_name)
    
    return response['url']