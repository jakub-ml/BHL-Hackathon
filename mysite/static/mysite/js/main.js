// Przykład dla React (można łatwo zaadaptować do Vue, HTML/CSS)

import React from 'react';
import './HomePage.css'; // Zakładam, że masz plik CSS

const HomePage = () => {
  return (
    <div className="home-page">
      <header className="hero-section">
        <h1>GreenCompute Optimizer</h1>
        <p className="subtitle">
          Minimalizuj ślad węglowy Twoich obliczeń cyfrowych
        </p>
        <p>
          Oszczędzaj planetę i redukuj koszty operacyjne, wybierając najbardziej
          ekologiczne centra danych dla Twoich zadań obliczeniowych.
        </p>
        <div className="cta-buttons">
          <button className="cta-primary">Rozpocznij Optymalizację</button>
          <button className="cta-secondary">Dowiedz się więcej</button>
        </div>
        <div className="hero-image-placeholder">
          {"/home/user/Obrazy/Zrzuty ekranu/Zrzut ekranu z 2025-11-30 00-07-27.png/"}
           
        </div>
      </header>

      <section className="features-section">
        <h2>Jak działamy?</h2>
        <div className="features-grid">
          <div className="feature-card">
            <h3>Szacowanie Emisji (Green Estimator)</h3>
            <p>
              Precyzyjnie oszacuj emisję CO2 dla Twoich zadań ML, AI i innych
              intensywnych obliczeń. Wprowadź parametry, a my zrobimy resztę.
            </p>
          </div>
          <div className="feature-card">
            <h3>Inteligentny Asystent AI</h3>
            <p>
              Nasz agent AI pomoże Ci szybko i dokładnie wprowadzić wszystkie
              niezbędne dane techniczne, ułatwiając proces.
            </p>
          </div>
          <div className="feature-card">
            <h3>Dynamiczna Rekomendacja Datacenter</h3>
            <p>
              Otrzymaj rekomendacje najbardziej ekologicznych centrów danych w
              czasie rzeczywistym, bazując na aktualnym miksie energetycznym i
              efektywności.
            </p>
          </div>
          <div className="feature-card">
            <h3>Analiza i Dashboard</h3>
            <p>
              Monitoruj swoje oszczędności CO2 i finansowe dzięki intuicyjnym
              raportom i wizualizacjom.
            </p>
          </div>
        </div>
      </section>

      <section className="benefits-section">
        <h2>Korzyści dla Twojej Firmy</h2>
        <ul>
          <li>Zmniejszenie śladu węglowego i zgodność z ESG</li>
          <li>Redukcja kosztów operacyjnych</li>
          <li>Uniknięcie kar za emisję CO2</li>
          <li>Poprawa wizerunku firmy jako innowacyjnej i ekologicznej</li>
          <li>Optymalne wykorzystanie zasobów obliczeniowych</li>
        </ul>
      </section>

      <section className="call-to-action-bottom">
        <h2>Gotowy, by zacząć?</h2>
        <p>
          Dołącz do rewolucji zielonych obliczeń już dziś!
        </p>
        <button className="cta-primary">Zarejestruj się</button>
      </section>
    </div>
  );
};

export default HomePage;