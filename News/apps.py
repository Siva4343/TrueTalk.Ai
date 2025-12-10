from django.apps import AppConfig


class NewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'News'
    
    def ready(self):
        """
        Start the news scheduler when Django starts.
        This will automatically fetch news every hour.
        """
        import os
        # Only run scheduler in the main process, not in reloader
        if os.environ.get('RUN_MAIN') == 'true':
            from .scheduler import start_scheduler
            start_scheduler()

