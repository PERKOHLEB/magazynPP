import streamlit as st
from supabase import create_client, Client

# Konfiguracja połączenia z Supabase
# Dane pobierane są z Streamlit Secrets dla bezpieczeństwa
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("📦 System Zarządzania Produktami")

# Wybór sekcji w sidebarze
menu = st.sidebar.radio("Nawigacja", ["Kategorie", "Produkty"])

# --- SEKCJA KATEGORIE ---
if menu == "Kategorie":
    st.header("📂 Zarządzanie Kategoriami")
    
    # Formularz dodawania
    with st.form("add_category"):
        st.subheader("Dodaj nową kategorię")
        nazwa_kat = st.text_input("Nazwa kategorii")
        opis_kat = st.text_area("Opis")
        submit_kat = st.form_submit_button("Dodaj kategorię")
        
        if submit_kat and nazwa_kat:
            data = {"nazwa": nazwa_kat, "opis": opis_kat}
            response = supabase.table("kategorie").insert(data).execute()
            st.success(f"Dodano kategorię: {nazwa_kat}")
            st.rerun()

    # Wyświetlanie i usuwanie
    st.subheader("Lista kategorii")
    kat_data = supabase.table("kategorie").select("*").execute()
    
    for kat in kat_data.data:
        col1, col2 = st.columns([4, 1])
        col1.write(f"**{kat['nazwa']}** - {kat['opis']}")
        if col2.button("Usuń", key=f"del_kat_{kat['id']}"):
            supabase.table("kategorie").delete().eq("id", kat['id']).execute()
            st.warning(f"Usunięto kategorię ID: {kat['id']}")
            st.rerun()

# --- SEKCJA PRODUKTY ---
elif menu == "Produkty":
    st.header("🛒 Zarządzanie Produktami")
    
    # Pobranie kategorii do selectboxa
    kat_data = supabase.table("kategorie").select("id, nazwa").execute()
    kategorie_dict = {k['nazwa']: k['id'] for k in kat_data.data}
    
    # Formularz dodawania produktu
    with st.form("add_product"):
        st.subheader("Dodaj nowy produkt")
        nazwa_prod = st.text_input("Nazwa produktu")
        liczba = st.number_input("Liczba sztuk", min_value=0, step=1)
        cena = st.number_input("Cena", min_value=0.0, step=0.01)
        kategoria_nazwa = st.selectbox("Kategoria", options=list(kategorie_dict.keys()))
        
        submit_prod = st.form_submit_button("Dodaj produkt")
        
        if submit_prod and nazwa_prod:
            prod_data = {
                "nazwa": nazwa_prod,
                "liczba": liczba,
                "cena": cena,
                "kategoria_id": kategorie_dict[kategoria_nazwa]
            }
            supabase.table("produkty").insert(prod_data).execute()
            st.success(f"Dodano produkt: {nazwa_prod}")
            st.rerun()

    # Wyświetlanie i usuwanie
    st.subheader("Lista produktów")
    prod_data = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
    
    if prod_data.data:
        for p in prod_data.data:
            col1, col2 = st.columns([4, 1])
            kat_name = p.get('kategorie', {}).get('nazwa', 'Brak')
            col1.write(f"**{p['nazwa']}** | Cena: {p['cena']} zł | Sztuk: {p['liczba']} | Kat: {kat_name}")
            if col2.button("Usuń", key=f"del_prod_{p['id']}"):
                supabase.table("produkty").delete().eq("id", p['id']).execute()
                st.warning(f"Usunięto produkt ID: {p['id']}")
                st.rerun()
    else:
        st.info("Brak produktów w bazie.")
