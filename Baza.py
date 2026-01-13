import streamlit as st
from supabase import create_client, Client

# Konfiguracja połączenia z Supabase
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Magazyn Supabase", layout="wide")
st.title("📦 System Zarządzania Magazynem")

# Wybór sekcji w sidebarze
menu = st.sidebar.radio("Nawigacja", ["Stany Magazynowe", "Kategorie", "Dodaj Produkt"])

# --- SEKCJA 1: STANY MAGAZYNOWE (PODGLĄD I USUWANIE) ---
if menu == "Stany Magazynowe":
    st.header("📊 Aktualne stany magazynowe")
    
    # Pobranie danych z złączeniem tabel (join), aby wyświetlić nazwę kategorii
    prod_data = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
    
    if prod_data.data:
        # Nagłówki kolumn
        col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns([3, 2, 2, 2, 1])
        col_h1.write("**Produkt**")
        col_h2.write("**Kategoria**")
        col_h3.write("**Cena**")
        col_h4.write("**Liczba sztuk**")
        col_h5.write("**Akcja**")
        st.divider()

        for p in prod_data.data:
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
            
            # Logika kolorowania
            liczba = p['liczba']
            color = "red" if liczba < 20 else "green"
            kat_name = p.get('kategorie', {}).get('nazwa', 'Brak')
            
            c1.write(p['nazwa'])
            c2.write(kat_name)
            c3.write(f"{p['cena']} zł")
            
            # Wyświetlanie liczby sztuk z kolorem
            c4.markdown(f":{color}[**{liczba} szt.**]")
            
            if c5.button("Usuń", key=f"del_p_{p['id']}"):
                supabase.table("produkty").delete().eq("id", p['id']).execute()
                st.rerun()
    else:
        st.info("Magazyn jest pusty.")

# --- SEKCJA 2: KATEGORIE ---
elif menu == "Kategorie":
    st.header("📂 Zarządzanie Kategoriami")
    
    with st.expander("➕ Dodaj nową kategorię"):
        with st.form("add_cat"):
            nazwa_kat = st.text_input("Nazwa kategorii")
            opis_kat = st.text_area("Opis")
            if st.form_submit_button("Zapisz"):
                supabase.table("kategorie").insert({"nazwa": nazwa_kat, "opis": opis_kat}).execute()
                st.success("Dodano kategorię!")
                st.rerun()

    kat_data = supabase.table("kategorie").select("*").execute()
    for kat in kat_data.data:
        col_a, col_b = st.columns([5, 1])
        col_a.write(f"**{kat['nazwa']}** — {kat['opis']}")
        if col_b.button("Usuń", key=f"del_k_{kat['id']}"):
            supabase.table("kategorie").delete().eq("id", kat['id']).execute()
            st.rerun()

# --- SEKCJA 3: DODAWANIE PRODUKTU ---
elif menu == "Dodaj Produkt":
    st.header("🛒 Dodaj nowy produkt do bazy")
    
    # Pobranie kategorii do listy rozwijanej
    kat_data = supabase.table("kategorie").select("id, nazwa").execute()
    kategorie_dict = {k['nazwa']: k['id'] for k in kat_data.data}
    
    if not kategorie_dict:
        st.warning("Najpierw dodaj przynajmniej jedną kategorię!")
    else:
        with st.form("new_product"):
            nazwa = st.text_input("Nazwa produktu")
            cena = st.number_input("Cena (zł)", min_value=0.0, step=0.01)
            liczba = st.number_input("Stan początkowy (sztuki)", min_value=0, step=1)
            kat_wybor = st.selectbox("Kategoria", options=list(kategorie_dict.keys()))
            
            if st.form_submit_button("Dodaj produkt"):
                new_data = {
                    "nazwa": nazwa,
                    "cena": cena,
                    "liczba": liczba,
                    "kategoria_id": kategorie_dict[kat_wybor]
                }
                supabase.table("produkty").insert(new_data).execute()
                st.success(f"Dodano produkt: {nazwa}")
