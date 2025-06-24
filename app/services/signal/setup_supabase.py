from app.supabase_media_service import SupabaseMediaService

def setup_supabase():
    """Configuration initiale de Supabase"""
    service = SupabaseMediaService()
    
    print("🔧 Configuration initiale Supabase...")
    
    # Créer le bucket pour les signalements
    service.create_bucket_if_not_exists()
    
    print("✅ Configuration Supabase terminée !")
    print(f"📁 Bucket '{service.bucket_name}' prêt à utiliser")
    print("🌐 URLs publiques accessibles immédiatement")

if __name__ == "__main__":
    setup_supabase()
