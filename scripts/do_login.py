"""Login helper - salva sessao do Instagram via instaloader."""
import instaloader

USERNAME = "monsoon_fc_"

L = instaloader.Instaloader()
try:
    L.interactive_login(USERNAME)
    L.save_session_to_file()
    print(f"\n[OK] Login realizado com sucesso!")
    print(f"[OK] Sessao salva para @{USERNAME}")
except Exception as e:
    print(f"[ERRO] {e}")
