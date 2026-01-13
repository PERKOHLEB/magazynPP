import streamlit as st
import pandas as pd
from supabase import create_client, Client

# Konfiguracja połączenia
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Magazyn Pro", layout="wide")

# --- FUNKCJE POMOCNICZE ---
def get_products_df():
    """Pobiera produkty i zwraca je jako DataFrame."""
    res = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
    if res.data:
        df = pd.DataFrame(res.data)
        # Wyciągamy nazwę kategorii z zagnieżdżonego słownika
        df['kategoria_nazwa'] = df['kategorie'].apply(lambda x: x.get('nazwa') if x else "Brak")
        return df
    return pd.DataFrame()

# --- MENU ---
menu = st.sidebar.radio("Nawigacja", ["Stany Magazynowe", "Edytor i Eksport", "Kategorie", "Dodaj Produkt"])

# --- SEKCJA 1: STANY MAGAZYNOWE (PODGLĄD) ---
if menu == "Stany Magazynowe":
    st.header("📊 Podgląd Magazynu")
    df = get_products_df()
    
    if not df.empty:
        # Wyświetlanie sformatowanej listy (z kolorami)
        for _, row in df.iterrows():
            col1, col2, col3 = st.columns([3, 2, 2])
            color = "red" if row['liczba'] < 20 else "green"
            
            col1.write(f"**{row['nazwa']}** ({row['kategoria_nazwa']})")
            col2.markdown(f"Stan: :{color}[**{row['liczba']} szt.**]")
            col3.write(f"Cena: {row['cena']} zł")
            st.divider()
    else:
        st.info("Brak danych.")

# --- SEKCJA 2: EDYTOR I EKSPORT (PROPOZYCJA 2 i 5) ---
elif menu == "Edytor i Eksport":
    st.header("✏️ Masowa Edycja i Eksport danych")
    
    df = get_products_df()
    
    if not df.empty:
        # --- PROPOZYCJA 5: EKSPORT DO CSV ---
        st.subheader("📥 Eksportuj dane")
        # Przygotowanie danych do CSV (bez zbędnych kolumn systemowych)
        csv_df = df[['id', 'nazwa', 'liczba', 'cena', 'kategoria_nazwa']]
        csv = csv_df.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="Pobierz tabelę jako CSV",
            data=csv,
            file_name="stan_magazynu.csv",
            mime="text/csv",
            help="Kliknij, aby pobrać dane do Excela"
        )
        
        st.divider()

        # --- PROPOZYCJA 2: EDYTOR (UPDATE) ---
        st.subheader("📝 Szybka edycja w tabeli")
        st.info("Możesz zmieniać wartości bezpośrednio w tabeli poniżej. Po edycji zatwierdź zmiany przyciskiem.")

        # Wyświetlamy edytowalną tabelę
        edited_df = st.data_editor(
            df[['id', 'nazwa', 'liczba', 'cena']], 
            key="product_editor",
            disabled=["id"], # ID nie powinno być edytowalne
            hide_index=True
        )

        if st.button("Zapisz zmiany w bazie"):
            try:
                for index, row in edited_df.iterrows():
                    # Aktualizujemy każdy wiersz w Supabase po ID
                    supabase.table("produkty").update({
                        "nazwa": row['nazwa'],
                        "liczba": row['liczba'],
                        "cena": float(row['cena'])
                    }).eq("id", row['id']).execute()
                st.success("Wszystkie zmiany zostały zapisane!")
                st.rerun()
            except Exception as e:
                st.error(f"Błąd podczas zapisu: {e}")
    else:
        st.warning("Brak danych do wyświetlenia.")

# --- SEKCJA 3: KATEGORIE ---
elif menu == "Kategorie":
    st.header("📂 Kategorie")
    # ... (kod z poprzedniej wersji) ...
    with st.form("add_cat"):
        nazwa = st.text_input("Nowa kategoria")
        if st.form_submit_button("Dodaj"):
            supabase.table("kategorie").insert({"nazwa": nazwa}).execute()
            st.rerun()

    kat_data = supabase.table("kategorie").select("*").execute()
    for k in kat_data.data:
        st.text(f"• {k['nazwa']}")

# --- SEKCJA 4: DODAWANIE PRODUKTU ---
elif menu == "Dodaj Produkt":
    st.header("🛒 Nowy Produkt")
    # ... (kod z poprzedniej wersji) ...
    kat_res = supabase.table("kategorie").select("id, nazwa").execute()
    kategorie_dict = {k['nazwa']: k['id'] for k in kat_res.data}
    
    with st.form("new_p"):
        nazwa = st.text_input("Nazwa")
        liczba = st.number_input("Sztuk", min_value=0)
        cena = st.number_input("Cena", min_value=0.0)
        kat = st.selectbox("Kategoria", options=list(kategorie_dict.keys()))
        if st.form_submit_button("Dodaj"):
            supabase.table("produkty").insert({
                "nazwa": nazwa, "liczba": liczba, "cena": cena, "kategoria_id": kategorie_dict[kat]
            }).execute()
            st.success("Dodano!")
