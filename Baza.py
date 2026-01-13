import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- KONFIGURACJA POŁĄCZENIA ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Magazyn Supabase", layout="wide")

# --- FUNKCJA POBIERANIA DANYCH ---
def get_products_df():
    try:
        res = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df['kategoria_nazwa'] = df['kategorie'].apply(lambda x: x.get('nazwa') if x else "Brak")
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Błąd bazy danych: {e}")
        return pd.DataFrame()

# --- SIDEBAR: KONFIGURACJA PROGU ---
st.sidebar.title("⚙️ Ustawienia")

# DODANE: Dynamiczne ustawianie poziomu niskiego stanu
low_stock_threshold = st.sidebar.number_input(
    "Próg niskiego stanu (szt.):", 
    min_value=0, 
    value=20, 
    step=5,
    help="Produkty poniżej tej ilości będą oznaczone na czerwono."
)

st.sidebar.divider()

# --- MENU BOCZNE ---
menu = st.sidebar.radio("Nawigacja", [
    "📊 Stany Magazynowe", 
    "🚨 Niski stan", 
    "✏️ Edycja i Eksport", 
    "📂 Kategorie", 
    "➕ Dodaj Produkt"
])

# --- SEKCJA 1: STANY MAGAZYNOWE ---
if menu == "📊 Stany Magazynowe":
    st.header("Wszystkie produkty")
    df = get_products_df()
    
    if not df.empty:
        col_h1, col_h2, col_h3, col_h4 = st.columns([3, 2, 2, 1])
        col_h1.write("**Produkt**")
        col_h2.write("**Kategoria**")
        col_h3.write("**Ilość**")
        col_h4.write("**Cena**")
        st.divider()

        for _, row in df.iterrows():
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            
            # ZMIENIONE: Użycie dynamicznego progu do kolorowania
            color = "red" if row['liczba'] < low_stock_threshold else "green"
            
            c1.write(row['nazwa'])
            c2.write(row['kategoria_nazwa'])
            c3.markdown(f":{color}[**{row['liczba']} szt.**]")
            c4.write(f"{row['cena']} zł")
            st.divider()
    else:
        st.info("Baza jest pusta.")

# --- SEKCJA 2: NISKI STAN (ZALEŻNY OD PROGU) ---
elif menu == "🚨 Niski stan":
    st.header(f"🚨 Produkty poniżej {low_stock_threshold} szt.")
    st.warning(f"Lista towarów, których stan jest mniejszy niż Twój próg ({low_stock_threshold}).")

    df = get_products_df()
    if not df.empty:
        # ZMIENIONE: Filtrowanie na podstawie dynamicznego progu
        low_stock_df = df[df['liczba'] < low_stock_threshold]

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
            st.success(f"Wszystkie produkty mają stan >= {low_stock_threshold}!")

# --- SEKCJA 3: EDYCJA I EKSPORT ---
elif menu == "✏️ Edycja i Eksport":
    st.header("Zarządzanie i CSV")
    df = get_products_df()
    
    if not df.empty:
        csv = df[['nazwa', 'liczba', 'cena', 'kategoria_nazwa']].to_csv(index=False).encode('utf-8')
        st.download_button("📥 Pobierz CSV", data=csv, file_name="magazyn.csv", mime="text/csv")
        
        st.subheader("Edytor")
        edited_df = st.data_editor(
            df[['id', 'nazwa', 'liczba', 'cena']], 
            hide_index=True, 
            disabled=["id"] 
        )
        
        if st.button("Zapisz zmiany"):
            for _, row in edited_df.iterrows():
                supabase.table("produkty").update({
                    "nazwa": row['nazwa'],
                    "liczba": row['liczba'], 
                    "cena": float(row['cena'])
                }).eq("id", row['id']).execute()
            st.success("Zaktualizowano bazę danych!")
            st.rerun()

# --- SEKCJA 4: KATEGORIE ---
elif menu == "📂 Kategorie":
    st.header("Kategorie")
    with st.form("new_cat"):
        n_kat = st.text_input("Nowa kategoria")
        if st.form_submit_button("Dodaj") and n_kat:
            supabase.table("kategorie").insert({"nazwa": n_kat}).execute()
            st.rerun()
    
    res = supabase.table("kategorie").select("*").execute()
    for k in res.data:
        st.write(f"• {k['nazwa']}")

# --- SEKCJA 5: DODAJ PRODUKT ---
elif menu == "➕ Dodaj Produkt":
    st.header("Nowy produkt")
    kats = supabase.table("kategorie").select("id, nazwa").execute()
    kat_dict = {k['nazwa']: k['id'] for k in kats.data}
    
    with st.form("add_p"):
        nazwa = st.text_input("Nazwa")
        liczba = st.number_input("Ilość", min_value=0)
        cena = st.number_input("Cena", min_value=0.0)
        wybrana_kat = st.selectbox("Kategoria", options=list(kat_dict.keys()))
        
        if st.form_submit_button("Dodaj"):
            supabase.table("produkty").insert({
                "nazwa": nazwa, "liczba": liczba, "cena": cena, "kategoria_id": kat_dict[wybrana_kat]
            }).execute()
            st.success("Dodano produkt.")
