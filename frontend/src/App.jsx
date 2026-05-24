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

  const [escortVehicleCount, setEscortVehicleCount] = useState(0);

  const [result, setResult] = useState(null);
  const [recentCalculations, setRecentCalculations] = useState([]);

  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState("");

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

  async function loadRecentCalculations() {
    try {
      const response = await axios.get(`${API_URL}/calculations/recent`, {
        params: {
          limit: 10,
        },
      });

      setRecentCalculations(response.data);
    } catch (error) {
      console.error(error);
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
    if (toCity && toQuery === toCity.name) {
      setToCities([]);
      return;
    }

    const timer = setTimeout(() => {
      searchCities(toQuery, setToCities);
    }, 300);

    return () => clearTimeout(timer);
  }, [toQuery, toCity]);

  useEffect(() => {
    loadRecentCalculations();
  }, []);

  function selectFromCity(city) {
    if (!city.has_coordinates) {
      setError(
        `У города "${city.name}" пока нет координат. Для расчёта выбери город с координатами.`
      );
      return;
    }

    setError("");
    setFromCity(city);
    setFromQuery(city.name);
    setFromCities([]);
  }

  function selectToCity(city) {
    if (!city.has_coordinates) {
      setError(
        `У города "${city.name}" пока нет координат. Для расчёта выбери город с координатами.`
      );
      return;
    }

    setError("");
    setToCity(city);
    setToQuery(city.name);
    setToCities([]);
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

    setCargoLength(15000);
    setCargoWidth(3490);
    setCargoHeight(3500);
    setCargoWeight(25);
    setEscortVehicleCount(0);

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

    if (!fromCity.has_coordinates) {
      return `У города отправления "${fromCity.name}" нет координат`;
    }

    if (!toCity.has_coordinates) {
      return `У города назначения "${toCity.name}" нет координат`;
    }

    const length = Number(cargoLength);
    const width = Number(cargoWidth);
    const height = Number(cargoHeight);
    const weight = Number(cargoWeight);
    const escortCount = Number(escortVehicleCount);

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

    if (!Number.isInteger(escortCount) || escortCount < 0) {
      return "Количество автомобилей прикрытия должно быть целым числом от 0";
    }

    if (escortCount > 10) {
      return "Количество автомобилей прикрытия выглядит слишком большим";
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
          escort_vehicle_count: Number(escortVehicleCount),
        });

      setResult(response.data);
      await loadRecentCalculations();
    } catch (error) {
      console.error(error);

      const detail = error.response?.data?.detail;

      if (typeof detail === "string") {
        setError(detail);
      } else if (detail?.message) {
        setError(detail.message);
      } else if (Array.isArray(detail)) {
        setError(
          detail
            .map((item) => item.msg || "Ошибка валидации")
            .join(". ")
        );
      } else {
        setError("Не удалось выполнить расчёт. Проверь параметры груза и маршрут");
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

  function CityMeta({ city }) {
    if (!city) return null;

    return (
      <div className="selected-city">
        <span>{city.subject_name || "Субъект не указан"}</span>
        <span>{city.tariff_zone_name || "Тарифная зона не указана"}</span>
        <span className={city.has_coordinates ? "ok" : "bad"}>
          {city.has_coordinates ? "координаты есть" : "нет координат"}
        </span>
      </div>
    );
  }

  function CitySuggestions({ cities, onSelect }) {
    if (cities.length === 0) return null;

    return (
      <div className="suggestions">
        {cities.map((city) => (
          <button
            key={city.id}
            type="button"
            onClick={() => onSelect(city)}
            className={`suggestion ${!city.has_coordinates ? "disabled-suggestion" : ""}`}
          >
            <span>{city.name}</span>

            <small>
              {city.subject_name || "Субъект не указан"}
              {city.tariff_zone_name ? ` · ${city.tariff_zone_name}` : ""}
              {city.has_coordinates ? "" : " · нет координат"}
            </small>
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className="page">
      <header className="header">
        <div>
          <p className="eyebrow">Калькулятор перевозки</p>
          <h1>Расчёт стоимости маршрута</h1>
          <p className="subtitle">
            Выбери города, укажи параметры груза, а система подберёт тариф,
            рассчитает дорожное расстояние через OSRM и сохранит результат.
          </p>
        </div>
      </header>

      <main className="layout">
        <section className="card">
          <div className="section-header">
            <h2>Новый расчёт</h2>

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

                    if (fromCity && event.target.value !== fromCity.name) {
                      setFromCity(null);
                    }
                  }}
                  placeholder="Например, Москва"
                />

                <CitySuggestions cities={fromCities} onSelect={selectFromCity} />
                <CityMeta city={fromCity} />
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

                    if (toCity && event.target.value !== toCity.name) {
                      setToCity(null);
                    }
                  }}
                  placeholder="Например, Иркутск"
                />

                <CitySuggestions cities={toCities} onSelect={selectToCity} />
                <CityMeta city={toCity} />
              </div>
            </div>

            <div className="grid">
              <div className="field">
                <label>Длина, мм</label>
                <input
                  type="number"
                  min="1"
                  value={cargoLength}
                  onChange={(event) => setCargoLength(event.target.value)}
                />
              </div>

              <div className="field">
                <label>Ширина, мм</label>
                <input
                  type="number"
                  min="1"
                  value={cargoWidth}
                  onChange={(event) => setCargoWidth(event.target.value)}
                />
              </div>

              <div className="field">
                <label>Высота, мм</label>
                <input
                  type="number"
                  min="1"
                  value={cargoHeight}
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
                  onChange={(event) => setCargoWeight(event.target.value)}
                />
              </div>

              <div className="field">
                  <label>Автомобили прикрытия, шт.</label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    step="1"
                    value={escortVehicleCount}
                    onChange={(event) => setEscortVehicleCount(event.target.value)}
                  />
                </div>
            </div>

            <p className="form-hint">
              Габариты указываются в миллиметрах, вес — в тоннах. Например:
              15000×3490×3500 мм, 25 т.
            </p>

            {error && <div className="error">{error}</div>}

            <button className="primary-button" type="submit" disabled={isCalculating}>
              {isCalculating ? "Считаем..." : "Рассчитать"}
            </button>
          </form>
        </section>

        <section className="card">
          <h2>Результат</h2>

          {!result && (
            <p className="muted">
              Заполни маршрут и параметры груза, затем нажми “Рассчитать”.
            </p>
          )}

          {result && (
              <div className="result">
                <div className="route">
                  <strong>{result.from_city}</strong>
                  <span>→</span>
                  <strong>{result.to_city}</strong>
                </div>

                <div className="chips">
                  <span>{result.direction_name}</span>
                  <span>{result.cargo_size_category_name}</span>
                  <span>
                    {result.from_tariff_zone_name || "—"} → {result.to_tariff_zone_name}
                  </span>
                </div>

                <div className="result-grid">
                  <div>
                    <span>Расстояние</span>
                    <strong>{formatNumber(result.distance_km)} км</strong>
                  </div>

                  <div>
                    <span>Базовая ставка</span>
                    <strong>
                      {formatMoney(result.base_rate_per_km, result.currency)} / км
                    </strong>
                  </div>

                  <div>
                    <span>Надбавка за габарит</span>
                    <strong>
                      {formatMoney(result.cargo_size_surcharge_per_km, result.currency)} / км
                    </strong>
                  </div>

                  <div>
                    <span>Итоговая ставка без прикрытия</span>
                    <strong>
                      {formatMoney(result.final_rate_per_km, result.currency)} / км
                    </strong>
                  </div>

                  <div>
                    <span>Базовая цена</span>
                    <strong>{formatMoney(result.base_price, result.currency)}</strong>
                  </div>

                  <div>
                    <span>Надбавка за габарит</span>
                    <strong>
                      {formatMoney(result.cargo_size_surcharge_price, result.currency)}
                    </strong>
                  </div>

                  <div>
                    <span>Автомобили прикрытия</span>
                    <strong>
                      {result.escort_vehicle_count} ×{" "}
                      {formatMoney(result.escort_vehicle_rate_per_km, result.currency)} / км
                    </strong>
                  </div>

                  <div>
                    <span>Стоимость прикрытия</span>
                    <strong>
                      {formatMoney(result.additional_services_price, result.currency)}
                    </strong>
                  </div>

                  <div className="total">
                    <span>Итого</span>
                    <strong>{formatMoney(result.final_price, result.currency)}</strong>
                  </div>
                </div>

                <div className="explanation">{result.explanation}</div>
              </div>
            )}
        </section>
      </main>

      <section className="card full-width">
        <div className="section-header">
          <h2>Последние расчёты</h2>
          <button type="button" onClick={loadRecentCalculations} className="ghost-button">
            Обновить
          </button>
        </div>

        {recentCalculations.length === 0 && (
          <p className="muted">Расчётов пока нет.</p>
        )}

        {recentCalculations.length > 0 && (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Маршрут</th>
                  <th>Груз</th>
                  <th>Расстояние</th>
                  <th>Итого</th>
                  <th>Дата</th>
                </tr>
              </thead>
              <tbody>
                {recentCalculations.map((item) => (
                  <tr key={item.id}>
                    <td>
                      {item.from_city_name || "—"} → {item.to_city_name || "—"}
                    </td>
                    <td>
                      {item.cargo_length_mm}×{item.cargo_width_mm}×
                      {item.cargo_height_mm} мм, {item.cargo_weight_tons} т
                      {item.cargo_size_category_name
                        ? ` · ${item.cargo_size_category_name}`
                        : ""}
                      {item.escort_vehicle_count
                        ? ` · прикрытие: ${item.escort_vehicle_count} шт.`
                        : ""}
                    </td>
                    <td>{formatNumber(item.distance_km)} км</td>
                    <td>{formatMoney(item.final_price, item.currency || "RUB")}</td>
                    <td>
                      {item.created_at
                        ? new Date(item.created_at).toLocaleString("ru-RU")
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

export default App;