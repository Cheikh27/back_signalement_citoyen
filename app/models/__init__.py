from app import db
# Importez tous les modèles ici
from .autres.appartenir_model import Appartenir
from .autres.groupe_model import Groupe
from .autres.tutoriel_model import Tutoriel
from .autres.suivre_model import Suivre


from .commentaire.commentairePetition_model import CommentairePetition
from .commentaire.commentairePublication_model import CommentairePublication
from .commentaire.commentaireSignalement_model import CommentaireSignalement

from .partage.partagePetition_model import PartagerPetition
from .partage.partagePublication_model import PartagerPublication
from .partage.partageSignalement_model import PartagerSignalement

from .reaction.appreciation_model import Appreciation
from .reaction.signature_model import Signature
from .reaction.vote_model import Vote

from .signal.petition_model import Petition
from .signal.publication_model import Publication
from .signal.signalement_model import Signalement

from .users.admin_model import Admin
from .users.autorite_model import Authorite
from .users.citoyen_model import Citoyen
from .users.moderateur_model import Moderateur
from .users.user_model import User

from .notification.notification_models import FCMToken, NotificationTemplate, NotificationAnalytics, NotificationPreferences, NotificationHistory





