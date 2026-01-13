import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- KONFIGURACJA POŁĄCZENIA Z SUPABASE ---
# Pamiętaj, aby dodać te dane w Streamlit Cloud -> Settings -> Secrets
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Zarządzanie Magazynem", layout="wide")

# --- FUNKCJA POBIERANIA DANYCH ---
def get_products_df():
    """Pobiera wszystkie produkty wraz z nazwami ich kategorii."""
    try:
        res = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            # Wyciągnięcie nazwy kategorii z relacji
            df['kategoria_nazwa'] = df['kategorie'].apply(lambda x: x.get('nazwa') if x else "Brak")
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Błąd bazy danych: {e}")
        return pd.DataFrame()

# --- MENU BOCZNE ---
st.sidebar.title("Magazyn v1.0")
menu = st.sidebar.radio("Nawigacja", [
    "📊 Stany Magazynowe", 
    "🚨 Niski stan (< 20)", 
    "✏️ Edycja i Eksport", 
    "📂 Kategorie", 
    "➕ Dodaj Produkt"
])

# --- SEKCJA 1: WSZYSTKIE STANY MAGAZYNOWE ---
if menu == "📊 Stany Magazynowe":
    st.header("Wszystkie produkty w magazynie")
    df = get_products_df()
    
    if not df.empty:
        col_h1, col_h2, col_h3, col_h4 = st.columns([3, 2, 2, 1])
        col_h1.write("**Nazwa produktu**")
        col_h2.write("**Kategoria**")
        col_h3.write("**Ilość**")
        col_h4.write("**Cena**")
        st.divider()

        for _, row in df.iterrows():
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            # Kolorowanie: czerwony poniżej 20, zielony 20 i więcej
            color = "red" if row['liczba'] < 20 else "green"
            
            c1.write(row['nazwa'])
            c2.write(row['kategoria_nazwa'])
            c3.markdown(f":{color}[**{row['liczba']} szt.**]")
            c4.write(f"{row['cena']} zł")
            st.divider()
    else:
        st.info("Brak produktów w bazie danych.")

# --- SEKCJA 2: TYLKO NISKI STAN (< 20 SZTUK) ---
elif menu == "🚨 Niski stan (< 20)":
    st.header("🚨 Produkty wymagające zamówienia")
    st.warning("Poniżej znajdują się towary, których stan spadł poniżej 20 sztuk.")

    df = get_products_df()
    if not df.empty:
        # Filtrowanie: tylko produkty poniżej 20 sztuk
        low_stock_df = df[df['liczba'] < 20]

        if not low_stock_df.empty:
            for _, row in low_stock_df.iterrows():
                with st.container():
                    c1, c2, c3 = st.columns([3, 2, 1])
                    c1.write(f"**{row['nazwa']}**")
                    c2.markdown(f"Aktualnie: :red[**{row['liczba']} szt.**]")
                    if c3.button("Usuń", key=f"del_{row['id']}"):
                        supabase.table("produkty").delete().eq("id", row['id']).execute()
                        st.rerun()
                    st.divider()
        else:
            st.success("Wszystkie produkty mają stan powyżej 20 sztuk!")

# --- SEKCJA 3: EDYCJA I EKSPORT ---
elif menu == "✏️ Edycja i Eksport":
    st.header("Zarządzanie danymi")
    df = get_products_df()
    
    if not df.empty:
        # Eksport do CSV
        csv = df[['nazwa', 'liczba', 'cena', 'kategoria_nazwa']].to_csv(index=False).encode('utf-8')
        st.download_button("📥 Pobierz listę (CSV)", data=csv, file_name="stan_magazynu.csv", mime="text/csv")
        
        st.subheader("Szybka edycja ilości i cen")
        # Edytowalna tabela
        edited_df = st.data_editor(
            df[['id', 'nazwa', 'liczba', 'cena']], 
            hide_index=True, 
            disabled=["id", "nazwa"] # Nazwa i ID zablokowane do edycji tutaj
        )
        
        if st.button("Zapisz zmiany"):
            for _, row in edited_df.iterrows():
                supabase.table("produkty").update({
                    "liczba": row['liczba'], 
                    "cena": float(row['cena'])
                }).eq("id", row['id']).execute()
            st.success("Dane zostały zaktualizowane!")
            st.rerun()

# --- SEKCJA 4: KATEGORIE ---
elif menu == "📂 Kategorie":
    st.header("Kategorie produktów")
    with st.form("new_cat"):
        nazwa_kat = st.text_input("Nazwa nowej kategorii")
        if st.form_submit_button("Dodaj kategorię") and nazwa_kat:
            supabase.table("kategorie").insert({"nazwa": nazwa_kat}).execute()
            st.rerun()
    
    res = supabase.table("kategorie").select("*").execute()
    for k in res.data:
        st.write(f"• {k['nazwa']}")

# --- SEKCJA 5: DODAJ PRODUKT ---
elif menu == "➕ Dodaj Produkt":
    st.header("Dodaj nowy towar")
    kats = supabase.table("kategorie").select("id, nazwa").execute()
    kat_dict = {k['nazwa']: k['id'] for k in kats.data}
    
    if not kat_dict:
        st.error("Najpierw dodaj kategorię!")
    else:
        with st.form("add_p"):
            nazwa = st.text_input("Nazwa produktu")
            liczba = st.number_input("Ilość", min_value=0, value=0)
            cena = st.number_input("Cena (zł)", min_value=0.0, value=0.0)
            wybrana_kat = st.selectbox("Kategoria", options=list(kat_dict.keys()))
            
            if st.form_submit_button("Dodaj do bazy"):
                if nazwa:
                    supabase.table("produkty").insert({
                        "nazwa": nazwa, 
                        "liczba": liczba, 
                        "cena": cena, 
                        "kategoria_id": kat_dict[wybrana_kat]
                    }).execute()
                    st.success(f"Dodano produkt: {nazwa}")
                else:
                    st.warning("Podaj nazwę produktu!")
