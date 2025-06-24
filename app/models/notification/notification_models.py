# app/models/fcm_models.py
from app.models import db
from datetime import datetime
from enum import Enum

class FCMToken(db.Model):
    """Stockage des tokens FCM/OneSignal pour notifications push"""
    __tablename__ = 'fcm_tokens'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.IDuser'), nullable=False)
    token = db.Column(db.String(255), nullable=False, unique=True)  # OneSignal Player ID ou FCM Token
    device_type = db.Column(db.String(20), nullable=False)  # 'android', 'ios', 'web'
    device_id = db.Column(db.String(255), nullable=True)
    app_version = db.Column(db.String(50), nullable=True)
    platform_info = db.Column(db.Text, nullable=True)  # JSON avec infos device
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)

    # Relations
    user = db.relationship('User', backref='fcm_tokens')

    def __repr__(self):
        return f"<FCMToken {self.id}: User {self.user_id} - {self.device_type}>"

    def to_dict(self):
        return {
            'id': self.id,
            'token': self.token,
            'device_type': self.device_type,
            'device_id': self.device_id,
            'app_version': self.app_version,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat()
        }

class NotificationHistory(db.Model):
    """Historique des notifications envoyées"""
    __tablename__ = 'notification_history'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.IDuser'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Métadonnées pour navigation
    entity_type = db.Column(db.String(50), nullable=True)  # 'signalement', 'petition', 'publication'
    entity_id = db.Column(db.Integer, nullable=True)
    
    # Statut d'envoi
    fcm_message_id = db.Column(db.String(255), nullable=True)
    sent_successfully = db.Column(db.Boolean, default=False)
    error_message = db.Column(db.Text, nullable=True)
    
    # Méthode de livraison
    delivery_method = db.Column(db.String(20), nullable=True)  # 'onesignal', 'supabase', 'both', 'failed'
    
    # Classification
    priority = db.Column(db.String(20), default='normal')  # 'low', 'normal', 'high', 'urgent'
    category = db.Column(db.String(50), default='general')  # 'signalement', 'petition', etc.
    
    # Engagement utilisateur
    is_read = db.Column(db.Boolean, default=False)
    clicked_at = db.Column(db.DateTime, nullable=True)
    
    # Expéditeur (optionnel)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.IDuser'), nullable=True)
    
    # Métadonnées supplémentaires
    notification_metadata = db.Column(db.Text, nullable=True)  # JSON
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relations
    user = db.relationship('User', foreign_keys=[user_id], backref='notification_history')
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_notifications')

    def __repr__(self):
        return f"<NotificationHistory {self.id}: {self.title} -> User {self.user_id}>"

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'priority': self.priority,
            'category': self.category,
            'is_read': self.is_read,
            'sent_successfully': self.sent_successfully,
            'delivery_method': self.delivery_method,
            'sender_id': self.sender_id,
            'created_at': self.created_at.isoformat(),
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None
        }

class NotificationPreferences(db.Model):
    """Préférences de notification par utilisateur"""
    __tablename__ = 'notification_preferences'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.IDuser'), nullable=False, unique=True)
    
    # Préférences par type de contenu
    nouveaux_signalements = db.Column(db.Boolean, default=True)
    commentaires_signalements = db.Column(db.Boolean, default=True)
    nouvelles_petitions = db.Column(db.Boolean, default=True)
    commentaires_petitions = db.Column(db.Boolean, default=True)
    nouvelles_publications = db.Column(db.Boolean, default=True)
    commentaires_publications = db.Column(db.Boolean, default=True)
    votes_signatures = db.Column(db.Boolean, default=True)
    reponses_autorites = db.Column(db.Boolean, default=True)
    mentions = db.Column(db.Boolean, default=True)
    changements_statut = db.Column(db.Boolean, default=True)
    
    # Préférences par canal
    notifications_push = db.Column(db.Boolean, default=True)
    notifications_realtime = db.Column(db.Boolean, default=True)
    notifications_email = db.Column(db.Boolean, default=False)
    
    # Préférences par priorité
    urgent_only = db.Column(db.Boolean, default=False)
    
    # Heures silencieuses
    quiet_hours_enabled = db.Column(db.Boolean, default=False)
    quiet_hours_start = db.Column(db.Time, nullable=True)  # Ex: 22:00
    quiet_hours_end = db.Column(db.Time, nullable=True)    # Ex: 08:00
    
    # Géolocalisation
    location_based = db.Column(db.Boolean, default=True)
    location_radius_km = db.Column(db.Integer, default=10)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    user = db.relationship('User', backref='notification_preferences')

    def __repr__(self):
        return f"<NotificationPreferences User {self.user_id}>"

    def to_dict(self):
        return {
            'nouveaux_signalements': self.nouveaux_signalements,
            'commentaires_signalements': self.commentaires_signalements,
            'nouvelles_petitions': self.nouvelles_petitions,
            'commentaires_petitions': self.commentaires_petitions,
            'nouvelles_publications': self.nouvelles_publications,
            'commentaires_publications': self.commentaires_publications,
            'votes_signatures': self.votes_signatures,
            'reponses_autorites': self.reponses_autorites,
            'mentions': self.mentions,
            'changements_statut': self.changements_statut,
            'notifications_push': self.notifications_push,
            'notifications_realtime': self.notifications_realtime,
            'notifications_email': self.notifications_email,
            'urgent_only': self.urgent_only,
            'quiet_hours_enabled': self.quiet_hours_enabled,
            'quiet_hours_start': self.quiet_hours_start.isoformat() if self.quiet_hours_start else None,
            'quiet_hours_end': self.quiet_hours_end.isoformat() if self.quiet_hours_end else None,
            'location_based': self.location_based,
            'location_radius_km': self.location_radius_km
        }

class NotificationTemplate(db.Model):
    """Templates de notifications pour réutilisation"""
    __tablename__ = 'notification_templates'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    title_template = db.Column(db.String(255), nullable=False)
    message_template = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.String(20), default='normal')
    icon_url = db.Column(db.String(500), nullable=True)
    variables = db.Column(db.Text, nullable=True)  # JSON des variables attendues
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<NotificationTemplate {self.name}>"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'title_template': self.title_template,
            'message_template': self.message_template,
            'category': self.category,
            'priority': self.priority,
            'icon_url': self.icon_url,
            'variables': self.variables,
            'is_active': self.is_active
        }

class NotificationAnalytics(db.Model):
    """Analytics des notifications pour métriques"""
    __tablename__ = 'notification_analytics'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.String(20), nullable=False)
    delivery_method = db.Column(db.String(20), nullable=False)
    
    # Métriques
    total_sent = db.Column(db.Integer, default=0)
    total_delivered = db.Column(db.Integer, default=0)
    total_read = db.Column(db.Integer, default=0)
    total_clicked = db.Column(db.Integer, default=0)
    avg_read_time_seconds = db.Column(db.Float, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<NotificationAnalytics {self.date} - {self.category}>"

    def to_dict(self):
        return {
            'date': self.date.isoformat(),
            'category': self.category,
            'priority': self.priority,
            'delivery_method': self.delivery_method,
            'total_sent': self.total_sent,
            'total_delivered': self.total_delivered,
            'total_read': self.total_read,
            'total_clicked': self.total_clicked,
            'avg_read_time_seconds': self.avg_read_time_seconds
        }