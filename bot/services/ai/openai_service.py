import asyncio
import aiohttp
from typing import Optional, Dict, Any
import json
import os

class OpenAIService:
    """Сервис для генерации контента через OpenAI API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"
        self.model = "gpt-3.5-turbo"

    async def generate_post_content(
        self,
        topic: str,
        theme: str,
        style: str = "friendly",
        language: str = "ru",
        content_length: str = "medium",
        max_length: int = 2000,
        is_premium: bool = False,
        prompt_template: Optional[str] = None,
        user_notes: Optional[str] = None,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Генерирует контент поста на основе темы и настроек
        
        Args:
            topic: Тема поста
            theme: Общая тематика (финансы, маркетинг и т.д.)
            style: Стиль написания (formal, friendly, humorous)
            language: Язык контента (ru/en)
            max_length: Максимальная длина контента
            is_premium: Использовать GPT-4 для премиум пользователей
            
        Returns:
            str: Сгенерированный контент или None в случае ошибки
        """
        if not self.api_key:
            # Заглушка для тестирования без API ключа
            return await self._generate_mock_content(topic, theme, style, language, content_length)
        
        try:
            prompt = self._build_prompt(topic, theme, style, language, content_length, max_length, prompt_template, user_notes)
            
            # Выбираем модель в зависимости от типа подписки
            model = "gpt-4" if is_premium else "gpt-3.5-turbo"
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Ты профессиональный копирайтер для социальных сетей."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    "max_tokens": max_length // 2,
                    "temperature": temperature
                }
                
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result["choices"][0]["message"]["content"].strip()
                        return content
                    else:
                        print(f"OpenAI API error: {response.status}")
                        return None
                        
        except Exception as e:
            print(f"Error generating content: {e}")
            return None
    
    def _build_prompt(self, topic: str, theme: str, style: str, language: str, content_length: str, max_length: int, prompt_template: Optional[str], user_notes: Optional[str]) -> str:
        """Строит промпт для генерации контента"""
        
        style_map = {
            "formal": "официальном и деловом",
            "friendly": "дружелюбном и простом", 
            "humorous": "юмористичном и легком"
        }
        
        # Конвертируем длину контента в количество слов
        length_map = {
            "short": {"ru": "до 50 слов", "en": "up to 50 words", "words": 50},
            "medium": {"ru": "до 100 слов", "en": "up to 100 words", "words": 100},
            "long": {"ru": "от 100 слов", "en": "100+ words", "words": 150}
        }
        
        style_text = style_map.get(style, "дружелюбном")
        length_info = length_map.get(content_length, length_map["medium"])
        
        base_prompt_ru = f"""
Напиши пост для социальной сети на тему "{topic}" в области "{theme}".

Требования:
- Стиль: {style_text}
- Язык: русский
- Длина: {length_info["ru"]}
- Структура: заголовок, основной текст, призыв к действию
- Используй эмодзи для привлечения внимания
- Делай текст читабельным и интересным
"""

        base_prompt_en = f"""
Write a social media post about "{topic}" in the "{theme}" niche.

Requirements:
- Style: {style_text.replace('ном', '')}
- Language: English
- Length: {length_info["en"]}
- Structure: headline, main text, call to action
- Use emojis to attract attention
- Make the text readable and engaging
"""

        additional_notes = f"\nДополнительные инструкции: {user_notes}\n" if user_notes and language == "ru" else (f"\nAdditional notes: {user_notes}\n" if user_notes else "")

        if prompt_template:
            prompt = prompt_template.format(topic=topic, theme=theme, style=style, language=language, length=length_info["en"] if language != "ru" else length_info["ru"]) + additional_notes
        else:
            prompt = (base_prompt_ru if language == "ru" else base_prompt_en) + additional_notes + (f"\nТема поста: {topic}\nТематика: {theme}\n" if language == "ru" else f"\nPost topic: {topic}\nTheme: {theme}\n")
        
        return prompt
    
    async def _generate_mock_content(self, topic: str, theme: str, style: str, language: str, content_length: str) -> str:
        """Генерирует заглушку для тестирования без API ключа"""
        
        # Имитируем задержку API
        await asyncio.sleep(1)
        
        if language == "ru":
            templates = {
                "финансы": [
                    f"💰 **{topic}**\n\n🔍 В мире финансов важно понимать основы. {topic} - это ключевой аспект успешного управления деньгами.\n\n📊 Основные принципы:\n• Планирование\n• Анализ рисков\n• Диверсификация\n\n💡 Помните: знания - ваш главный капитал!\n\n👍 Согласны? Поделитесь мнением в комментариях!",
                    f"🚀 **{topic}** - тема, которая волнует многих!\n\n💼 В современном мире финансовой грамотности недостаточно просто зарабатывать. Нужно уметь:\n• Сохранять капитал\n• Приумножать средства\n• Защищаться от инфляции\n\n🎯 Изучайте, применяйте, достигайте целей!\n\n#финансы #инвестиции #деньги"
                ],
                "маркетинг": [
                    f"🎯 **{topic}**\n\n📈 Эффективный маркетинг начинается с понимания потребностей клиентов. {topic} помогает создать связь между брендом и аудиторией.\n\n🔥 Ключевые моменты:\n• Исследование рынка\n• Персонализация\n• Измерение результатов\n\n✨ Успех приходит к тем, кто действует!\n\n💬 Какой ваш опыт в маркетинге?"
                ],
                "технологии": [
                    f"⚡ **{topic}**\n\n🤖 Технологии меняют наш мир каждый день. {topic} - это возможность быть на шаг впереди.\n\n🔧 Важные аспекты:\n• Непрерывное обучение\n• Адаптация к изменениям\n• Практическое применение\n\n🌟 Будущее уже здесь!\n\n👨‍💻 Используете ли вы новые технологии в работе?"
                ],
                "психология": [
                    f"🧠 **{topic}**\n\n💭 Психология помогает понять себя и окружающих. {topic} - важная тема для личностного роста.\n\n🔍 Ключевые аспекты:\n• Самопознание\n• Эмпатия\n• Развитие навыков\n\n💡 Познание себя - путь к успеху!\n\n🤔 Как вы относитесь к этой теме?"
                ],
                "здоровье": [
                    f"🏥 **{topic}**\n\n💪 Здоровье - главная ценность в жизни. {topic} помогает поддерживать хорошее самочувствие.\n\n🌟 Важные принципы:\n• Регулярность\n• Баланс\n• Профилактика\n\n💚 Заботьтесь о себе каждый день!\n\n❤️ Как вы поддерживаете свое здоровье?"
                ],
                "образование": [
                    f"📚 **{topic}**\n\n🎓 Образование открывает новые возможности. {topic} - важный шаг в развитии.\n\n📖 Основы обучения:\n• Постоянство\n• Практика\n• Применение знаний\n\n🚀 Учитесь, развивайтесь, достигайте целей!\n\n📝 Какие темы вас интересуют больше всего?"
                ],
                "спорт": [
                    f"⚽ **{topic}**\n\n🏃‍♂️ Спорт укрепляет тело и дух. {topic} - путь к здоровому образу жизни.\n\n💪 Преимущества спорта:\n• Физическая форма\n• Ментальная сила\n• Дисциплина\n\n🏆 Побеждайте каждый день!\n\n🎯 Каким спортом занимаетесь?"
                ],
                "путешествия": [
                    f"✈️ **{topic}**\n\n🌍 Путешествия расширяют горизонты. {topic} - возможность открыть новый мир.\n\n🗺️ Преимущества путешествий:\n• Новые впечатления\n• Культурный обмен\n• Личностный рост\n\n🌟 Открывайте мир вместе с нами!\n\n🌎 Какие места мечтаете посетить?"
                ],
                "еда": [
                    f"🍕 **{topic}**\n\n👨‍🍳 Кулинария - это искусство и наука. {topic} приносит радость и удовольствие.\n\n🍽️ Основы кулинарии:\n• Качественные ингредиенты\n• Терпение\n• Творческий подход\n\n😋 Наслаждайтесь каждым блюдом!\n\n🍴 Какое ваше любимое блюдо?"
                ],
                "мода": [
                    f"👗 **{topic}**\n\n✨ Мода - способ самовыражения. {topic} помогает создать уникальный стиль.\n\n👠 Элементы стиля:\n• Индивидуальность\n• Комфорт\n• Уверенность\n\n💃 Будьте собой в любом образе!\n\n👔 Какой ваш стиль?"
                ],
                "развлечения": [
                    f"🎬 **{topic}**\n\n🎭 Развлечения делают жизнь ярче. {topic} - источник позитивных эмоций.\n\n🎪 Виды развлечений:\n• Кино и сериалы\n• Музыка\n• Игры\n\n🎉 Наслаждайтесь каждым моментом!\n\n🎮 Что вас больше всего развлекает?"
                ],
                "бизнес": [
                    f"💼 **{topic}**\n\n🚀 Бизнес требует стратегического мышления. {topic} - ключ к успеху.\n\n📊 Основы бизнеса:\n• Планирование\n• Анализ\n• Адаптация\n\n💡 Инвестируйте в знания!\n\n🏢 Какой у вас опыт в бизнесе?"
                ],
                "образ_жизни": [
                    f"🌟 **{topic}**\n\n💫 Образ жизни формирует нашу реальность. {topic} - путь к лучшей жизни.\n\n✨ Принципы здорового образа жизни:\n• Баланс\n• Осознанность\n• Развитие\n\n🌈 Создавайте жизнь своей мечты!\n\n💝 Какой ваш идеальный образ жизни?"
                ]
            }
        else:
            templates = {
                "finance": [
                    f"💰 **{topic}**\n\n🔍 Understanding finances is crucial in today's world. {topic} is a key aspect of successful money management.\n\n📊 Core principles:\n• Planning\n• Risk analysis\n• Diversification\n\n💡 Remember: knowledge is your main capital!\n\n👍 Do you agree? Share your thoughts in comments!",
                ],
                "marketing": [
                    f"🎯 **{topic}**\n\n📈 Effective marketing starts with understanding customer needs. {topic} helps create a connection between brand and audience.\n\n🔥 Key points:\n• Market research\n• Personalization\n• Measuring results\n\n✨ Success comes to those who take action!\n\n💬 What's your marketing experience?"
                ],
                "tech": [
                    f"⚡ **{topic}**\n\n🤖 Technology changes our world every day. {topic} is an opportunity to stay one step ahead.\n\n🔧 Important aspects:\n• Continuous learning\n• Adapting to changes\n• Practical application\n\n🌟 The future is already here!\n\n👨‍💻 Do you use new technologies at work?"
                ],
                "psychology": [
                    f"🧠 **{topic}**\n\n💭 Psychology helps understand ourselves and others. {topic} is an important topic for personal growth.\n\n🔍 Key aspects:\n• Self-knowledge\n• Empathy\n• Skill development\n\n💡 Self-knowledge is the path to success!\n\n🤔 How do you feel about this topic?"
                ],
                "health": [
                    f"🏥 **{topic}**\n\n💪 Health is the main value in life. {topic} helps maintain good well-being.\n\n🌟 Important principles:\n• Regularity\n• Balance\n• Prevention\n\n💚 Take care of yourself every day!\n\n❤️ How do you maintain your health?"
                ],
                "education": [
                    f"📚 **{topic}**\n\n🎓 Education opens new opportunities. {topic} is an important step in development.\n\n📖 Learning basics:\n• Consistency\n• Practice\n• Knowledge application\n\n🚀 Learn, develop, achieve goals!\n\n📝 What topics interest you most?"
                ],
                "sports": [
                    f"⚽ **{topic}**\n\n🏃‍♂️ Sports strengthen body and spirit. {topic} is the path to a healthy lifestyle.\n\n💪 Benefits of sports:\n• Physical fitness\n• Mental strength\n• Discipline\n\n🏆 Win every day!\n\n🎯 What sports do you do?"
                ],
                "travel": [
                    f"✈️ **{topic}**\n\n🌍 Travel expands horizons. {topic} is an opportunity to discover a new world.\n\n🗺️ Benefits of travel:\n• New experiences\n• Cultural exchange\n• Personal growth\n\n🌟 Discover the world with us!\n\n🌎 What places do you dream of visiting?"
                ],
                "food": [
                    f"🍕 **{topic}**\n\n👨‍🍳 Cooking is art and science. {topic} brings joy and pleasure.\n\n🍽️ Cooking basics:\n• Quality ingredients\n• Patience\n• Creative approach\n\n😋 Enjoy every dish!\n\n🍴 What's your favorite dish?"
                ],
                "fashion": [
                    f"👗 **{topic}**\n\n✨ Fashion is a way of self-expression. {topic} helps create a unique style.\n\n👠 Style elements:\n• Individuality\n• Comfort\n• Confidence\n\n💃 Be yourself in any look!\n\n👔 What's your style?"
                ],
                "entertainment": [
                    f"🎬 **{topic}**\n\n🎭 Entertainment makes life brighter. {topic} is a source of positive emotions.\n\n🎪 Types of entertainment:\n• Movies and series\n• Music\n• Games\n\n🎉 Enjoy every moment!\n\n🎮 What entertains you most?"
                ],
                "business": [
                    f"💼 **{topic}**\n\n🚀 Business requires strategic thinking. {topic} is the key to success.\n\n📊 Business basics:\n• Planning\n• Analysis\n• Adaptation\n\n💡 Invest in knowledge!\n\n🏢 What's your business experience?"
                ],
                "lifestyle": [
                    f"🌟 **{topic}**\n\n💫 Lifestyle shapes our reality. {topic} is the path to a better life.\n\n✨ Healthy lifestyle principles:\n• Balance\n• Mindfulness\n• Development\n\n🌈 Create the life of your dreams!\n\n💝 What's your ideal lifestyle?"
                ]
            }
        
        # Выбираем шаблон
        theme_key = theme.lower() if language == "en" else theme
        # Маппинг русских тематик к ключам шаблонов
        theme_mapping = {
            "финансы": "финансы",
            "маркетинг": "маркетинг", 
            "технологии": "технологии",
            "психология": "психология",
            "здоровье": "здоровье",
            "образование": "образование",
            "спорт": "спорт",
            "путешествия": "путешествия",
            "еда": "еда",
            "мода": "мода",
            "развлечения": "развлечения",
            "бизнес": "бизнес",
            "образ_жизни": "образ_жизни"
        }
        
        # Для английского языка
        if language == "en":
            theme_mapping = {
                "finance": "finance",
                "marketing": "marketing",
                "tech": "tech", 
                "psychology": "psychology",
                "health": "health",
                "education": "education",
                "sports": "sports",
                "travel": "travel",
                "food": "food",
                "fashion": "fashion",
                "entertainment": "entertainment",
                "business": "business",
                "lifestyle": "lifestyle"
            }
        
        mapped_theme = theme_mapping.get(theme_key, theme_key)
        template_list = templates.get(mapped_theme, list(templates.values())[0])
        
        import random
        return random.choice(template_list)
    
    async def test_connection(self) -> bool:
        """Тестирует подключение к OpenAI API"""
        if not self.api_key:
            return False
            
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers
                ) as response:
                    return response.status == 200
                    
        except Exception:
            return False 