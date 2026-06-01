import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "";

function App() {
  const [fromQuery, setFromQuery] = useState("");
  const [toQuery, setToQuery] = useState("");

  const [fromCities, setFromCities] = useState([]);
  const [toCities, setToCities] = useState([]);

  const [fromCity, setFromCity] = useState(null);
  const [toCity, setToCity] = useState(null);

  const [cargoLength, setCargoLength] = useState(15000);
  const [cargoWidth, setCargoWidth] = useState(3490);
  const [cargoHeight, setCargoHeight] = useState(3500);
  const [cargoWeight, setCargoWeight] = useState(25);

  const [result, setResult] = useState(null);

  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState("");

  const [fromCityError, setFromCityError] = useState("");
  const [toCityError, setToCityError] = useState("");
  const [calculationError, setCalculationError] = useState("");

  async function searchCities(query, setter) {
    if (!query.trim()) {
      setter([]);
      return;
    }

    try {
      const response = await axios.get(`${API_URL}/cities`, {
        params: {
          query,
          limit: 10,
        },
      });

      setter(response.data);
    } catch (error) {
      console.error(error);
      setError("Не удалось загрузить список городов");
    }
  }


  useEffect(() => {
    if (fromCity && fromQuery === fromCity.name) {
      setFromCities([]);
      return;
    }

    const timer = setTimeout(() => {
      searchCities(fromQuery, setFromCities);
    }, 300);

    return () => clearTimeout(timer);
  }, [fromQuery, fromCity]);

  useEffect(() => {
      function handleDocumentClick(event) {
        const target = event.target;

        if (!(target instanceof Element)) return;

        if (target.closest(".field")) return;

        setFromCities([]);
        setToCities([]);
      }

      document.addEventListener("mousedown", handleDocumentClick);

      return () => {
        document.removeEventListener("mousedown", handleDocumentClick);
      };
    }, []);

  useEffect(() => {
    if (toCity && toQuery === toCity.name) {
      setToCities([]);
      return;
    }

    const timer = setTimeout(() => {
      searchCities(toQuery, setToCities);
    }, 300);

    return () => clearTimeout(timer);
  }, [toQuery, toCity]);


  function selectFromCity(city) {
      setError("");
      setCalculationError("");
      setFromCityError("");
      setFromCity(city);
      setFromQuery(city.name);
      setFromCities([]);
    }

  function selectToCity(city) {
      setError("");
      setCalculationError("");
      setToCityError("");
      setToCity(city);
      setToQuery(city.name);
      setToCities([]);
  }

  function normalizeCityName(value) {
      return value.trim().toLowerCase().replaceAll("ё", "е");
    }

    function findExactCityMatch(query, cities) {
      const normalizedQuery = normalizeCityName(query);

      if (!normalizedQuery) return null;

      return (
        cities.find((city) => normalizeCityName(city.name) === normalizedQuery) ||
        null
      );
    }

async function resolveCityOnBlur({
  query,
  selectedCity,
  cities,
  setCity,
  setCities,
  setCityError,
}) {
  const trimmedQuery = query.trim();

  if (!trimmedQuery) {
    setCity(null);
    setCityError("");
    setCities([]);
    return;
  }

  if (selectedCity && normalizeCityName(selectedCity.name) === normalizeCityName(trimmedQuery)) {
    setCityError("");
    setCities([]);
    return;
  }

  let exactMatch = findExactCityMatch(trimmedQuery, cities);

  if (!exactMatch) {
    try {
      const response = await axios.get(`${API_URL}/cities`, {
        params: {
          query: trimmedQuery,
          limit: 10,
        },
      });

      exactMatch = findExactCityMatch(trimmedQuery, response.data);
    } catch (error) {
      console.error(error);
    }
  }

  if (exactMatch) {
    setCity(exactMatch);
    setCityError("");
    setCities([]);
    return;
  }

  setCity(null);
  setCityError("Город не найден");
  setCities([]);
}

  function swapCities() {
    const oldFromCity = fromCity;
    const oldFromQuery = fromQuery;

    setFromCity(toCity);
    setFromQuery(toQuery);

    setToCity(oldFromCity);
    setToQuery(oldFromQuery);

    setFromCities([]);
    setToCities([]);
    setResult(null);
    setError("");
  }

  function clearForm() {
    setFromQuery("");
    setToQuery("");
    setFromCities([]);
    setToCities([]);
    setFromCity(null);
    setToCity(null);

    setCargoLength("");
    setCargoWidth("");
    setCargoHeight("");
    setCargoWeight("");

    setResult(null);
    setError("");
  }

  function validateForm() {
    if (!fromCity) {
      return "Выберите город отправления из списка";
    }

    if (!toCity) {
      return "Выберите город назначения из списка";
    }

    if (fromCity.id === toCity.id) {
      return "Город отправления и город назначения не должны совпадать";
    }

    const length = Number(cargoLength);
    const width = Number(cargoWidth);
    const height = Number(cargoHeight);
    const weight = Number(cargoWeight);

    if (!Number.isFinite(length) || length <= 0) {
      return "Длина груза должна быть больше 0";
    }

    if (!Number.isFinite(width) || width <= 0) {
      return "Ширина груза должна быть больше 0";
    }

    if (!Number.isFinite(height) || height <= 0) {
      return "Высота груза должна быть больше 0";
    }

    if (!Number.isFinite(weight) || weight <= 0) {
      return "Вес груза должен быть больше 0";
    }

    if (length > 100000) {
      return "Длина груза выглядит слишком большой. Проверь значение в миллиметрах";
    }

    if (width > 10000) {
      return "Ширина груза выглядит слишком большой. Проверь значение в миллиметрах";
    }

    if (height > 10000) {
      return "Высота груза выглядит слишком большой. Проверь значение в миллиметрах";
    }

    if (weight > 200) {
      return "Вес груза выглядит слишком большим. Проверь значение в тоннах";
    }

    return "";
  }

  async function handleCalculate(event) {
    event.preventDefault();

    setCalculationError("");
    setError("");
    setResult(null);

    const validationError = validateForm();

    if (validationError) {
      setError(validationError);
      return;
    }

    setIsCalculating(true);

    try {
      const response = await axios.post(`${API_URL}/calculate`, {
        from_city_id: fromCity.id,
        to_city_id: toCity.id,
        cargo_length_mm: Number(cargoLength),
        cargo_width_mm: Number(cargoWidth),
        cargo_height_mm: Number(cargoHeight),
        cargo_weight_tons: Number(cargoWeight),
      });

      setResult(response.data);
    } catch (error) {
      console.error(error);

      const detail = error.response?.data?.detail;

      if (typeof detail === "string") {
        setCalculationError(
          "Предварительный расчёт по выбранному маршруту не выполнен. Оставьте заявку или обратитесь к менеджеру, чтобы мы рассчитали стоимость вручную."
        );
      } else if (detail?.message) {
        setCalculationError(
          "Предварительный расчёт по выбранному маршруту не выполнен. Оставьте заявку или обратитесь к менеджеру, чтобы мы рассчитали стоимость вручную."
        );
      } else if (Array.isArray(detail)) {
        setError(
          detail
            .map((item) => item.msg || "Ошибка валидации")
            .join(". ")
        );
      } else {
        setCalculationError(
          "Предварительный расчёт по выбранному маршруту не выполнен. Оставьте заявку или обратитесь к менеджеру, чтобы мы рассчитали стоимость вручную."
        );
      }
    } finally {
      setIsCalculating(false);
    }
  }

  function formatMoney(value, currency = "RUB") {
    if (value === null || value === undefined) return "—";

    return new Intl.NumberFormat("ru-RU", {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }).format(Number(value));
  }

  function formatNumber(value, digits = 1) {
    if (value === null || value === undefined) return "—";

    const number = Number(value);

    if (!Number.isFinite(number)) return "—";

    return number
      .toLocaleString("ru-RU", {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      })
      .replace(",", ".");
  }

  function CitySuggestions({ cities, onSelect }) {
  if (cities.length === 0) return null;

  return (
    <div className="suggestions">
      {cities.map((city) => (
        <button
          key={city.id}
          type="button"
          onMouseDown={(event) => {
            event.preventDefault();
            onSelect(city);
          }}
          className="suggestion"
        >
          <span>{city.name}</span>

          <small>
            {city.subject_name || "Субъект не указан"}
            {city.tariff_zone_name ? ` · ${city.tariff_zone_name}` : ""}
          </small>
        </button>
      ))}
    </div>
  );
}

  function ResultChips({ result }) {
    const chips =
      result.calculation_type === "fixed"
        ? [result.cargo_size_category_name]
        : [result.direction_name, result.cargo_size_category_name];

    return (
      <div className="chips">
        {chips
          .filter((chip) => chip && chip !== "—")
          .map((chip) => (
            <span key={chip}>{chip}</span>
          ))}
      </div>
    );
  }

  return (
    <div className="page">
      <header className="header">
          <div>
            <p className="eyebrow">ТК ТАЛИ · калькулятор</p>
            <h1>Расчёт стоимости перевозки</h1>
            <p className="subtitle">
              Укажите маршрут и параметры груза — калькулятор подберёт тариф и рассчитает стоимость.
            </p>
          </div>
        </header>

      <main className="layout">
        <section className="card">
          <div className="section-header">
            <h2>Параметры перевозки</h2>

            <button type="button" onClick={clearForm} className="ghost-button">
              Очистить
            </button>
          </div>

          <form onSubmit={handleCalculate} className="form">
            <div className="route-fields">
              <div className="field">
                <label>Город отправления</label>
                <input
                  value={fromQuery}
                  onChange={(event) => {
                    setFromQuery(event.target.value);
                    setFromCityError("");

                    if (fromCity && event.target.value !== fromCity.name) {
                      setFromCity(null);
                    }
                  }}
                  onBlur={() => {
                    setTimeout(() => {
                      resolveCityOnBlur({
                        query: fromQuery,
                        selectedCity: fromCity,
                        cities: fromCities,
                        setCity: setFromCity,
                        setCities: setFromCities,
                        setCityError: setFromCityError,
                      });
                    }, 150);
                  }}
                  placeholder="Например, Москва"
                />

                <div className="field-error-wrapper">
                  {fromCityError && <span className="field-error">Город не найден</span>}
                </div>

                <CitySuggestions cities={fromCities} onSelect={selectFromCity} />
              </div>

              <button
                type="button"
                className="swap-button"
                onClick={swapCities}
                disabled={!fromQuery && !toQuery}
                title="Поменять города местами"
              >
                ⇄
              </button>

              <div className="field">
                <label>Город назначения</label>
                <input
                  value={toQuery}
                  onChange={(event) => {
                    setToQuery(event.target.value);
                    setToCityError("");

                    if (toCity && event.target.value !== toCity.name) {
                      setToCity(null);
                    }
                  }}
                  onBlur={() => {
                    setTimeout(() => {
                      resolveCityOnBlur({
                        query: toQuery,
                        selectedCity: toCity,
                        cities: toCities,
                        setCity: setToCity,
                        setCities: setToCities,
                        setCityError: setToCityError,
                      });
                    }, 150);
                  }}
                  placeholder="Например, Иркутск"
                />

                <div className="field-error-wrapper">
                  {toCityError && <span className="field-error">Город не найден</span>}
                </div>

                <CitySuggestions cities={toCities} onSelect={selectToCity} />
              </div>
            </div>

            <div className="grid">
              <div className="field">
                <label>Длина, мм</label>
                <input
                  type="number"
                  min="1"
                  value={cargoLength}
                  placeholder="мм"
                  onChange={(event) => setCargoLength(event.target.value)}
                />
              </div>

              <div className="field">
                <label>Ширина, мм</label>
                <input
                  type="number"
                  min="1"
                  value={cargoWidth}
                  placeholder="мм"
                  onChange={(event) => setCargoWidth(event.target.value)}
                />
              </div>

              <div className="field">
                <label>Высота, мм</label>
                <input
                  type="number"
                  min="1"
                  value={cargoHeight}
                  placeholder="мм"
                  onChange={(event) => setCargoHeight(event.target.value)}
                />
              </div>

              <div className="field">
                <label>Вес, т</label>
                <input
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={cargoWeight}
                  placeholder="т"
                  onChange={(event) => setCargoWeight(event.target.value)}
                />
              </div>
            </div>

            {error && <div className="error">{error}</div>}

            <button className="primary-button" type="submit" disabled={isCalculating}>
              {isCalculating ? "Считаем..." : "Рассчитать стоимость"}
            </button>
          </form>
        </section>

        <section className="card">
          <h2>Стоимость</h2>

          {!result && !calculationError && (
              <p className="muted">
                Заполните маршрут и параметры груза, затем нажмите “Рассчитать стоимость”
              </p>
            )}

            {calculationError && (
              <div className="calculation-error">
                <strong>Требует уточнения</strong>
                <p>{calculationError}</p>
              </div>
            )}

          {result && !calculationError && (
            <div className="result">
              <div className="route">
                <strong>{result.from_city}</strong>
                <span>→</span>
                <strong>{result.to_city}</strong>
              </div>

              <ResultChips result={result} />

              {result.calculation_type === "fixed" ? (
                <div className="result-grid">
                  <div>
                    <span>Расстояние</span>
                    <strong>{formatNumber(result.distance_km)} км</strong>
                  </div>

                  <div>
                    <span>Фиксированная цена</span>
                    <strong>{formatMoney(result.fixed_price, result.currency)}</strong>
                  </div>

                  <div className="total">
                    <span>Итого</span>
                    <strong>{formatMoney(result.final_price, result.currency)}</strong>
                  </div>
                </div>
                ) : (
                  <div className="result-grid">
                    <div>
                      <span>Расстояние</span>
                      <strong>{formatNumber(result.distance_km)} км</strong>
                    </div>

                    <div>
                      <span>Ставка</span>
                      <strong>
                        {formatMoney(result.final_rate_per_km, result.currency)} / км
                      </strong>
                    </div>


                    <div className="total">
                      <span>Итого</span>
                      <strong>{formatMoney(result.final_price, result.currency)}</strong>
                    </div>
                  </div>
                )}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;