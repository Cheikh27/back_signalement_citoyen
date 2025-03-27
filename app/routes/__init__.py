# Importer les blueprints
from .autres.appartenir_route import appartenir_bp
from .autres.groupe_route import groupe_bp

from .commentaire.commentairePetition_route import commentaire_petition_bp
from .commentaire.commentairePublication_route import commentaire_publication_bp
from .commentaire.commentaireSignalement_route import commentaire_signalement_bp

from .partage.partagePetition_route import partager_petition_bp
from .partage.partagePublication_route import partager_publication_bp
from .partage.partageSignalement_route import partager_signalement_bp

from .reaction.appreciation_route import appreciation_bp
from .reaction.signature_route import signature_bp
from .reaction.vote_route import vote_bp

from .signal.petition_route import petition_bp
from .signal.publication_route import publication_bp
from .signal.signalement_route import signalement_bp

from .users.admin_route import admin_bp
from .users.autorite_route import autorite_bp
from .users.citoyen_route import citoyen_bp
from .users.moderateur_route import moderateur_bp
from .users.user_route import user_bp
