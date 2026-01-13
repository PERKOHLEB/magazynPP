import streamlit as st
import pandas as pd
import math
from supabase import create_client, Client

# --- POŁĄCZENIE I FUNKCJE (bez zmian) ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def get_products_df():
    res = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
    if res.data:
        df = pd.DataFrame(res.data)
        df['kategoria_nazwa'] = df['kategorie'].apply(lambda x: x.get('nazwa') if x else "Brak")
        return df
    return pd.DataFrame()

# --- MENU (Dodano nową zakładkę) ---
menu = st.sidebar.radio("Nawigacja", [
    "Stany Magazynowe", 
    "⚠️ Ostrzeżenia", # <--- NOWA ZAKŁADKA
    "Edytor i Eksport", 
    "Kategorie", 
    "Dodaj Produkt"
])

# --- SEKCJA: OSTRZEŻENIA (15% NAJMNIEJSZYCH STANÓW) ---
if menu == "⚠️ Ostrzeżenia":
    st.header("⚠️ Produkty na wyczerpaniu")
    st.info("Poniższa lista zawiera 15% produktów z najniższym stanem magazynowym w Twojej bazie.")

    df = get_products_df()

    if not df.empty:
        total_products = len(df)
        # Obliczamy ile to jest 15% (zaokrąglając w górę, żeby zawsze coś pokazać)
        n_to_show = math.ceil(total_products * 0.15)
        
        # Sortujemy po liczbie sztuk i bierzemy n_to_show rekordów
        low_stock_df = df.sort_values(by='liczba', ascending=True).head(n_to_show)

        st.write(f"Wyświetlam {n_to_show} z {total_products} produktów.")

        # Wyświetlanie w formie ostrzegawczych kafelków
        for _, row in low_stock_df.iterrows():
            with st.container():
                # Używamy st.error dla efektu "czerwonego alarmu"
                st.error(f"**PRODUKT: {row['nazwa']}**")
                col1, col2, col3 = st.columns(3)
                col1.metric("Aktualny stan", f"{row['liczba']} szt.")
                col2.metric("Kategoria", row['kategoria_nazwa'])
                col3.metric("Wartość (cena)", f"{row['cena']} zł")
                st.divider()
    else:
        st.warning("Baza produktów jest pusta. Nie można wyliczyć ostrzeżeń.")

# --- RESZTA KODU (Stany, Edytor itd. - bez zmian) ---
elif menu == "Stany Magazynowe":
    st.header("📊 Podgląd Magazynu")
    # ... (Twój poprzedni kod)
