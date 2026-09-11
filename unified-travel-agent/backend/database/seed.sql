-- Reference data seed. Adding a new city/flight/hotel here (or via INSERT at
-- runtime) is all that's needed to teach the agents about it - no code changes.

INSERT INTO destinations (city, sights, food, best_season)
SELECT * FROM (VALUES
    ('KYOTO',
     ARRAY['Fushimi Inari Shrine', 'Kinkaku-ji (Golden Pavilion)', 'Arashiyama Bamboo Grove'],
     ARRAY['Matcha Parfait', 'Kaiseki Dining', 'Yudofu'],
     'Spring (Cherry Blossoms) or Autumn'),
    ('PARIS',
     ARRAY['Eiffel Tower', 'Louvre Museum', 'Montmartre & Sacré-Cœur'],
     ARRAY['Croissants', 'Duck Confit', 'Macarons'],
     'Late Spring to Early Autumn'),
    ('VANCOUVER',
     ARRAY['Stanley Park Seawall', 'Capilano Suspension Bridge', 'Granville Island Market'],
     ARRAY['Wild Pacific Salmon', 'Poutine', 'Fresh Oysters'],
     'Summer (July-September)')
) AS v(city, sights, food, best_season)
WHERE NOT EXISTS (SELECT 1 FROM destinations);

-- destination uses city names (matching hotels.city / destinations.city),
-- not airport codes, so city lookups (search, cancellation) match consistently.
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time)
SELECT * FROM (VALUES
    ('JFK', 'PARIS', 'AF-007', 'Air France', 650.00, '10:30 AM'),
    ('JFK', 'PARIS', 'DL-212', 'Delta Air Lines', 580.00, '04:15 PM'),
    ('SFO', 'VANCOUVER', 'AC-881', 'Air Canada', 310.00, '08:00 AM'),
    ('LAX', 'KYOTO', 'JL-061', 'Japan Airlines', 920.00, '11:45 PM'),
    ('JFK', 'PARIS', 'UA-404', 'United Airlines', 610.00, '06:00 PM')
) AS v(origin, destination, flight_no, airline, price, departure_time)
WHERE NOT EXISTS (SELECT 1 FROM flights);

INSERT INTO hotels (city, name, rating, price_per_night, amenities)
SELECT * FROM (VALUES
    ('PARIS', 'Le Petit Boutique Hotel', 4.8, 210.00, 'Free WiFi, Breakfast'),
    ('PARIS', 'Grand Hotel De Ville', 4.5, 160.00, 'Pool, Spa'),
    ('KYOTO', 'Ryokan Cultural Stay', 4.9, 290.00, 'Onsen, Garden View'),
    ('VANCOUVER', 'Pacific View Suites', 4.6, 175.00, 'Fitness Center, Ocean View')
) AS v(city, name, rating, price_per_night, amenities)
WHERE NOT EXISTS (SELECT 1 FROM hotels);

-- 75 additional countries/destinations, generated to extend the demo catalog.
-- Idempotent: destinations use ON CONFLICT; flights/hotels are only inserted if
-- the destination has none yet (checked at seed time, not via a DB constraint).

INSERT INTO destinations (city, sights, food, best_season) VALUES ('NEW YORK', ARRAY['Statue of Liberty','Central Park','Times Square'], ARRAY['Bagels','New York Pizza','Cheesecake'], 'Year-round (Spring/Fall best)') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('LHR', 'NEW YORK', 'BA-115', 'British Airways', 620.0, '09:15 AM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('NEW YORK', 'New York Grand Hotel', 4.3, 120.0, 'Free WiFi, Breakfast');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('NEW YORK', 'New York Boutique Stay', 4.0, 80.0, 'Fitness Center, Concierge');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('LONDON', ARRAY['Big Ben','British Museum','Tower Bridge'], ARRAY['Fish and Chips','Sunday Roast','Afternoon Tea'], 'Late Spring to Early Autumn') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'LONDON', 'VS-004', 'Virgin Atlantic', 540.0, '07:40 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('LONDON', 'London Grand Hotel', 4.4, 145.0, 'Pool, Spa');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('LONDON', 'London Boutique Stay', 4.1, 98.0, 'Garden, Restaurant');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('ROME', ARRAY['Colosseum','Vatican Museums','Trevi Fountain'], ARRAY['Carbonara','Gelato','Suppli'], 'Spring or Autumn') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'ROME', 'AZ-609', 'ITA Airways', 560.0, '10:05 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('ROME', 'Rome Grand Hotel', 4.5, 170.0, 'Rooftop Bar, City View');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('ROME', 'Rome Boutique Stay', 4.2, 116.0, 'Historic Building, Concierge');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('BARCELONA', ARRAY['Sagrada Familia','Park Guell','La Rambla'], ARRAY['Paella','Tapas','Crema Catalana'], 'Late Spring to Early Autumn') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'BARCELONA', 'IB-6251', 'Iberia', 530.0, '06:20 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('BARCELONA', 'Barcelona Grand Hotel', 4.6, 195.0, 'Fitness Center, Concierge');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('BARCELONA', 'Barcelona Boutique Stay', 4.3, 134.0, 'Beachfront, Spa');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('BERLIN', ARRAY['Brandenburg Gate','Museum Island','East Side Gallery'], ARRAY['Currywurst','Pretzels','Schnitzel'], 'Summer (June-August)') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'BERLIN', 'LH-402', 'Lufthansa', 570.0, '05:50 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('BERLIN', 'Berlin Grand Hotel', 4.7, 220.0, 'Garden, Restaurant');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('BERLIN', 'Berlin Boutique Stay', 4.4, 152.0, 'Airport Shuttle, Breakfast');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('ATHENS', ARRAY['Acropolis','Plaka District','National Archaeological Museum'], ARRAY['Moussaka','Souvlaki','Baklava'], 'Spring or Autumn') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'ATHENS', 'A3-273', 'Aegean Airlines', 610.0, '10:30 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('ATHENS', 'Athens Grand Hotel', 4.8, 245.0, 'Historic Building, Concierge');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('ATHENS', 'Athens Boutique Stay', 4.0, 170.0, 'Free WiFi, Breakfast');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('LISBON', ARRAY['Belem Tower','Alfama District','Jeronimos Monastery'], ARRAY['Pasteis de Nata','Bacalhau','Grilled Sardines'], 'Spring to Early Autumn') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'LISBON', 'TP-208', 'TAP Air Portugal', 500.0, '08:10 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('LISBON', 'Lisbon Grand Hotel', 4.3, 270.0, 'Beachfront, Spa');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('LISBON', 'Lisbon Boutique Stay', 4.1, 188.0, 'Pool, Spa');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('AMSTERDAM', ARRAY['Rijksmuseum','Anne Frank House','Canal Ring'], ARRAY['Stroopwafels','Bitterballen','Dutch Cheese'], 'Spring (Tulip season) or Summer') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'AMSTERDAM', 'KL-642', 'KLM', 545.0, '06:00 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('AMSTERDAM', 'Amsterdam Grand Hotel', 4.4, 295.0, 'Airport Shuttle, Breakfast');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('AMSTERDAM', 'Amsterdam Boutique Stay', 4.2, 206.0, 'Rooftop Bar, City View');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('ZURICH', ARRAY['Lake Zurich','Old Town','Uetliberg'], ARRAY['Fondue','Rosti','Swiss Chocolate'], 'Summer (June-September)') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'ZURICH', 'LX-16', 'Swiss International', 590.0, '07:05 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('ZURICH', 'Zurich Grand Hotel', 4.5, 320.0, 'Free WiFi, Breakfast');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('ZURICH', 'Zurich Boutique Stay', 4.3, 80.0, 'Fitness Center, Concierge');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('VIENNA', ARRAY['Schonbrunn Palace','St. Stephen''s Cathedral','Belvedere Palace'], ARRAY['Wiener Schnitzel','Sachertorte','Apple Strudel'], 'Spring or Autumn') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'VIENNA', 'OS-89', 'Austrian Airlines', 575.0, '06:35 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('VIENNA', 'Vienna Grand Hotel', 4.6, 345.0, 'Pool, Spa');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('VIENNA', 'Vienna Boutique Stay', 4.4, 98.0, 'Garden, Restaurant');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('BRUSSELS', ARRAY['Grand Place','Atomium','Manneken Pis'], ARRAY['Belgian Waffles','Moules-Frites','Belgian Chocolate'], 'Late Spring to Early Autumn') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'BRUSSELS', 'SN-509', 'Brussels Airlines', 520.0, '05:15 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('BRUSSELS', 'Brussels Grand Hotel', 4.7, 120.0, 'Rooftop Bar, City View');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('BRUSSELS', 'Brussels Boutique Stay', 4.0, 116.0, 'Historic Building, Concierge');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('DUBLIN', ARRAY['Trinity College','Guinness Storehouse','Temple Bar'], ARRAY['Irish Stew','Soda Bread','Fish and Chips'], 'Summer (May-September)') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'DUBLIN', 'EI-105', 'Aer Lingus', 480.0, '09:00 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('DUBLIN', 'Dublin Grand Hotel', 4.8, 145.0, 'Fitness Center, Concierge');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('DUBLIN', 'Dublin Boutique Stay', 4.1, 134.0, 'Beachfront, Spa');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('STOCKHOLM', ARRAY['Gamla Stan','Vasa Museum','Djurgarden'], ARRAY['Swedish Meatballs','Cinnamon Buns','Gravlax'], 'Summer (June-August)') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'STOCKHOLM', 'SK-903', 'SAS', 560.0, '06:45 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('STOCKHOLM', 'Stockholm Grand Hotel', 4.3, 170.0, 'Garden, Restaurant');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('STOCKHOLM', 'Stockholm Boutique Stay', 4.2, 152.0, 'Airport Shuttle, Breakfast');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('OSLO', ARRAY['Vigeland Park','Viking Ship Museum','Oslo Opera House'], ARRAY['Salmon','Brunost','Norwegian Waffles'], 'Summer (May-September)') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'OSLO', 'SK-935', 'SAS', 565.0, '07:20 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('OSLO', 'Oslo Grand Hotel', 4.4, 195.0, 'Historic Building, Concierge');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('OSLO', 'Oslo Boutique Stay', 4.3, 170.0, 'Free WiFi, Breakfast');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('COPENHAGEN', ARRAY['Nyhavn','Tivoli Gardens','The Little Mermaid'], ARRAY['Smorrebrod','Danish Pastries','New Nordic Cuisine'], 'Summer (May-September)') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'COPENHAGEN', 'SK-941', 'SAS', 555.0, '06:10 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('COPENHAGEN', 'Copenhagen Grand Hotel', 4.5, 220.0, 'Beachfront, Spa');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('COPENHAGEN', 'Copenhagen Boutique Stay', 4.4, 188.0, 'Pool, Spa');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('HELSINKI', ARRAY['Suomenlinna','Senate Square','Design District'], ARRAY['Karelian Pies','Salmon Soup','Rye Bread'], 'Summer (June-August)') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'HELSINKI', 'AY-6', 'Finnair', 585.0, '10:50 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('HELSINKI', 'Helsinki Grand Hotel', 4.6, 245.0, 'Airport Shuttle, Breakfast');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('HELSINKI', 'Helsinki Boutique Stay', 4.0, 206.0, 'Rooftop Bar, City View');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('REYKJAVIK', ARRAY['Blue Lagoon','Hallgrimskirkja','Golden Circle'], ARRAY['Icelandic Lamb','Skyr','Fish Stew'], 'Summer (June-August) or Winter for Northern Lights') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'REYKJAVIK', 'FI-614', 'Icelandair', 410.0, '11:59 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('REYKJAVIK', 'Reykjavik Grand Hotel', 4.7, 270.0, 'Free WiFi, Breakfast');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('REYKJAVIK', 'Reykjavik Boutique Stay', 4.1, 80.0, 'Fitness Center, Concierge');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('WARSAW', ARRAY['Old Town','Royal Castle','Lazienki Park'], ARRAY['Pierogi','Bigos','Kielbasa'], 'Late Spring to Early Autumn') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'WARSAW', 'LO-27', 'LOT Polish Airlines', 500.0, '07:55 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('WARSAW', 'Warsaw Grand Hotel', 4.8, 295.0, 'Pool, Spa');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('WARSAW', 'Warsaw Boutique Stay', 4.2, 98.0, 'Garden, Restaurant');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('PRAGUE', ARRAY['Charles Bridge','Prague Castle','Old Town Square'], ARRAY['Trdelnik','Goulash','Czech Beer'], 'Spring or Autumn') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'PRAGUE', 'OK-105', 'Czech Airlines', 515.0, '06:15 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('PRAGUE', 'Prague Grand Hotel', 4.3, 320.0, 'Rooftop Bar, City View');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('PRAGUE', 'Prague Boutique Stay', 4.3, 116.0, 'Historic Building, Concierge');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('BUDAPEST', ARRAY['Parliament Building','Fisherman''s Bastion','Szechenyi Thermal Baths'], ARRAY['Goulash','Chimney Cake','Langos'], 'Spring or Autumn') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'BUDAPEST', 'LO-701', 'LOT Polish Airlines', 520.0, '08:35 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('BUDAPEST', 'Budapest Grand Hotel', 4.4, 345.0, 'Fitness Center, Concierge');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('BUDAPEST', 'Budapest Boutique Stay', 4.4, 134.0, 'Beachfront, Spa');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('ISTANBUL', ARRAY['Hagia Sophia','Blue Mosque','Grand Bazaar'], ARRAY['Kebabs','Baklava','Turkish Tea'], 'Spring or Autumn') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'ISTANBUL', 'TK-4', 'Turkish Airlines', 600.0, '11:15 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('ISTANBUL', 'Istanbul Grand Hotel', 4.5, 120.0, 'Garden, Restaurant');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('ISTANBUL', 'Istanbul Boutique Stay', 4.0, 152.0, 'Airport Shuttle, Breakfast');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('MOSCOW', ARRAY['Red Square','Kremlin','Saint Basil''s Cathedral'], ARRAY['Borscht','Pelmeni','Blini'], 'Summer (May-September)') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'MOSCOW', 'SU-100', 'Aeroflot', 650.0, '01:20 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('MOSCOW', 'Moscow Grand Hotel', 4.6, 145.0, 'Historic Building, Concierge');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('MOSCOW', 'Moscow Boutique Stay', 4.1, 170.0, 'Free WiFi, Breakfast');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('CAIRO', ARRAY['Pyramids of Giza','Egyptian Museum','Khan el-Khalili'], ARRAY['Koshari','Falafel','Molokhia'], 'Autumn to Spring (cooler months)') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'CAIRO', 'MS-986', 'EgyptAir', 640.0, '11:40 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('CAIRO', 'Cairo Grand Hotel', 4.7, 170.0, 'Beachfront, Spa');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('CAIRO', 'Cairo Boutique Stay', 4.2, 188.0, 'Pool, Spa');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('MARRAKESH', ARRAY['Jemaa el-Fnaa','Bahia Palace','Majorelle Garden'], ARRAY['Tagine','Couscous','Mint Tea'], 'Spring or Autumn') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'MARRAKESH', 'AT-201', 'Royal Air Maroc', 590.0, '09:25 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('MARRAKESH', 'Marrakesh Grand Hotel', 4.8, 195.0, 'Airport Shuttle, Breakfast');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('MARRAKESH', 'Marrakesh Boutique Stay', 4.3, 206.0, 'Rooftop Bar, City View');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('CAPE TOWN', ARRAY['Table Mountain','Robben Island','V&A Waterfront'], ARRAY['Bobotie','Biltong','Braai'], 'Summer (November-March)') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'CAPE TOWN', 'DL-200', 'Delta Air Lines', 950.0, '08:00 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('CAPE TOWN', 'Cape Town Grand Hotel', 4.3, 220.0, 'Free WiFi, Breakfast');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('CAPE TOWN', 'Cape Town Boutique Stay', 4.4, 80.0, 'Fitness Center, Concierge');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('NAIROBI', ARRAY['Nairobi National Park','Giraffe Centre','Karen Blixen Museum'], ARRAY['Nyama Choma','Ugali','Sukuma Wiki'], 'Dry seasons (June-Oct, Jan-Feb)') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'NAIROBI', 'KQ-536', 'Kenya Airways', 880.0, '10:10 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('NAIROBI', 'Nairobi Grand Hotel', 4.4, 245.0, 'Pool, Spa');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('NAIROBI', 'Nairobi Boutique Stay', 4.0, 98.0, 'Garden, Restaurant');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('ZANZIBAR', ARRAY['Stone Town','Spice Farms','Nungwi Beach'], ARRAY['Zanzibar Pizza','Seafood Curry','Spiced Coffee'], 'June to October') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'ZANZIBAR', 'KQ-118', 'Kenya Airways', 920.0, '10:40 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('ZANZIBAR', 'Zanzibar Grand Hotel', 4.5, 270.0, 'Rooftop Bar, City View');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('ZANZIBAR', 'Zanzibar Boutique Stay', 4.1, 116.0, 'Historic Building, Concierge');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('LAGOS', ARRAY['Lekki Conservation Centre','Nike Art Gallery','Tarkwa Bay Beach'], ARRAY['Jollof Rice','Suya','Egusi Soup'], 'November to February (dry season)') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'LAGOS', 'DL-32', 'Delta Air Lines', 870.0, '10:25 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('LAGOS', 'Lagos Grand Hotel', 4.6, 295.0, 'Fitness Center, Concierge');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('LAGOS', 'Lagos Boutique Stay', 4.2, 134.0, 'Beachfront, Spa');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('DUBAI', ARRAY['Burj Khalifa','Dubai Mall','Palm Jumeirah'], ARRAY['Shawarma','Al Machboos','Arabic Coffee'], 'November to March') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'DUBAI', 'EK-202', 'Emirates', 720.0, '10:55 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('DUBAI', 'Dubai Grand Hotel', 4.7, 320.0, 'Garden, Restaurant');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('DUBAI', 'Dubai Boutique Stay', 4.3, 152.0, 'Airport Shuttle, Breakfast');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('DOHA', ARRAY['Museum of Islamic Art','Souq Waqif','The Pearl-Qatar'], ARRAY['Machbous','Hummus','Karak Tea'], 'November to March') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'DOHA', 'QR-702', 'Qatar Airways', 700.0, '08:30 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('DOHA', 'Doha Grand Hotel', 4.8, 345.0, 'Historic Building, Concierge');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('DOHA', 'Doha Boutique Stay', 4.4, 170.0, 'Free WiFi, Breakfast');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('RIYADH', ARRAY['Kingdom Centre Tower','Diriyah','National Museum'], ARRAY['Kabsa','Jareesh','Dates'], 'November to February') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'RIYADH', 'SV-31', 'Saudia', 730.0, '11:05 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('RIYADH', 'Riyadh Grand Hotel', 4.3, 120.0, 'Beachfront, Spa');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('RIYADH', 'Riyadh Boutique Stay', 4.0, 188.0, 'Pool, Spa');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('JERUSALEM', ARRAY['Old City','Western Wall','Mount of Olives'], ARRAY['Hummus','Falafel','Shakshuka'], 'Spring or Autumn') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'JERUSALEM', 'LY-2', 'El Al', 680.0, '11:50 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('JERUSALEM', 'Jerusalem Grand Hotel', 4.4, 145.0, 'Airport Shuttle, Breakfast');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('JERUSALEM', 'Jerusalem Boutique Stay', 4.1, 206.0, 'Rooftop Bar, City View');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('AMMAN', ARRAY['Roman Theatre','Citadel Hill','Rainbow Street'], ARRAY['Mansaf','Falafel','Knafeh'], 'Spring or Autumn') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'AMMAN', 'RJ-262', 'Royal Jordanian', 660.0, '10:15 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('AMMAN', 'Amman Grand Hotel', 4.5, 170.0, 'Free WiFi, Breakfast');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('AMMAN', 'Amman Boutique Stay', 4.2, 80.0, 'Fitness Center, Concierge');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('DELHI', ARRAY['Red Fort','India Gate','Qutub Minar'], ARRAY['Butter Chicken','Chaat','Biryani'], 'October to March') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'DELHI', 'AI-102', 'Air India', 780.0, '01:30 AM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('DELHI', 'Delhi Grand Hotel', 4.6, 195.0, 'Pool, Spa');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('DELHI', 'Delhi Boutique Stay', 4.3, 98.0, 'Garden, Restaurant');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('KATHMANDU', ARRAY['Durbar Square','Swayambhunath','Boudhanath Stupa'], ARRAY['Momos','Dal Bhat','Newari Cuisine'], 'Autumn (Sept-Nov) or Spring') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'KATHMANDU', 'QR-648', 'Qatar Airways (via Doha)', 900.0, '09:45 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('KATHMANDU', 'Kathmandu Grand Hotel', 4.7, 220.0, 'Rooftop Bar, City View');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('KATHMANDU', 'Kathmandu Boutique Stay', 4.4, 116.0, 'Historic Building, Concierge');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('COLOMBO', ARRAY['Galle Face Green','National Museum','Gangaramaya Temple'], ARRAY['Rice and Curry','Hoppers','Kottu'], 'December to March') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'COLOMBO', 'UL-504', 'SriLankan Airlines', 870.0, '09:00 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('COLOMBO', 'Colombo Grand Hotel', 4.8, 245.0, 'Fitness Center, Concierge');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('COLOMBO', 'Colombo Boutique Stay', 4.0, 134.0, 'Beachfront, Spa');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('BANGKOK', ARRAY['Grand Palace','Wat Arun','Chatuchak Market'], ARRAY['Pad Thai','Tom Yum','Mango Sticky Rice'], 'November to February') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('LAX', 'BANGKOK', 'TG-794', 'Thai Airways', 820.0, '11:30 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('BANGKOK', 'Bangkok Grand Hotel', 4.3, 270.0, 'Garden, Restaurant');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('BANGKOK', 'Bangkok Boutique Stay', 4.1, 152.0, 'Airport Shuttle, Breakfast');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('HANOI', ARRAY['Old Quarter','Hoan Kiem Lake','Temple of Literature'], ARRAY['Pho','Banh Mi','Egg Coffee'], 'October to December') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('LAX', 'HANOI', 'VN-98', 'Vietnam Airlines', 790.0, '12:15 AM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('HANOI', 'Hanoi Grand Hotel', 4.4, 295.0, 'Historic Building, Concierge');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('HANOI', 'Hanoi Boutique Stay', 4.2, 170.0, 'Free WiFi, Breakfast');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('SIEM REAP', ARRAY['Angkor Wat','Angkor Thom','Ta Prohm'], ARRAY['Amok','Khmer Curry','Lok Lak'], 'November to February') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('LAX', 'SIEM REAP', 'QR-836', 'Qatar Airways (via Doha)', 850.0, '10:20 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('SIEM REAP', 'Siem Reap Grand Hotel', 4.5, 320.0, 'Beachfront, Spa');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('SIEM REAP', 'Siem Reap Boutique Stay', 4.3, 188.0, 'Pool, Spa');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('LUANG PRABANG', ARRAY['Kuang Si Falls','Mount Phousi','Royal Palace Museum'], ARRAY['Laap','Sticky Rice','Or Lam'], 'November to February') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('LAX', 'LUANG PRABANG', 'QV-458', 'Lao Airlines', 860.0, '09:50 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('LUANG PRABANG', 'Luang Prabang Grand Hotel', 4.6, 345.0, 'Airport Shuttle, Breakfast');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('LUANG PRABANG', 'Luang Prabang Boutique Stay', 4.4, 206.0, 'Rooftop Bar, City View');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('YANGON', ARRAY['Shwedagon Pagoda','Sule Pagoda','Circular Train'], ARRAY['Mohinga','Tea Leaf Salad','Shan Noodles'], 'November to February') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('LAX', 'YANGON', 'TG-303', 'Thai Airways (via Bangkok)', 880.0, '11:00 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('YANGON', 'Yangon Grand Hotel', 4.7, 120.0, 'Free WiFi, Breakfast');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('YANGON', 'Yangon Boutique Stay', 4.0, 80.0, 'Fitness Center, Concierge');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('KUALA LUMPUR', ARRAY['Petronas Towers','Batu Caves','Merdeka Square'], ARRAY['Nasi Lemak','Satay','Char Kway Teow'], 'Year-round (Dec-Feb driest)') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('LAX', 'KUALA LUMPUR', 'MH-89', 'Malaysia Airlines', 810.0, '11:45 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('KUALA LUMPUR', 'Kuala Lumpur Grand Hotel', 4.8, 145.0, 'Pool, Spa');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('KUALA LUMPUR', 'Kuala Lumpur Boutique Stay', 4.1, 98.0, 'Garden, Restaurant');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('SINGAPORE', ARRAY['Marina Bay Sands','Gardens by the Bay','Sentosa Island'], ARRAY['Chicken Rice','Laksa','Chili Crab'], 'Year-round (Feb-Apr driest)') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('LAX', 'SINGAPORE', 'SQ-38', 'Singapore Airlines', 950.0, '12:35 AM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('SINGAPORE', 'Singapore Grand Hotel', 4.3, 170.0, 'Rooftop Bar, City View');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('SINGAPORE', 'Singapore Boutique Stay', 4.2, 116.0, 'Historic Building, Concierge');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('BALI', ARRAY['Uluwatu Temple','Ubud Rice Terraces','Seminyak Beach'], ARRAY['Nasi Goreng','Satay','Babi Guling'], 'April to October') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('LAX', 'BALI', 'GA-56', 'Garuda Indonesia', 870.0, '01:10 AM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('BALI', 'Bali Grand Hotel', 4.4, 195.0, 'Fitness Center, Concierge');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('BALI', 'Bali Boutique Stay', 4.3, 134.0, 'Beachfront, Spa');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('MANILA', ARRAY['Intramuros','Rizal Park','National Museum of the Philippines'], ARRAY['Adobo','Sinigang','Lechon'], 'December to February') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('LAX', 'MANILA', 'PR-103', 'Philippine Airlines', 760.0, '11:55 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('MANILA', 'Manila Grand Hotel', 4.5, 220.0, 'Garden, Restaurant');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('MANILA', 'Manila Boutique Stay', 4.4, 152.0, 'Airport Shuttle, Breakfast');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('BEIJING', ARRAY['Great Wall of China','Forbidden City','Temple of Heaven'], ARRAY['Peking Duck','Dumplings','Hot Pot'], 'Spring or Autumn') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('LAX', 'BEIJING', 'CA-988', 'Air China', 800.0, '01:40 AM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('BEIJING', 'Beijing Grand Hotel', 4.6, 245.0, 'Historic Building, Concierge');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('BEIJING', 'Beijing Boutique Stay', 4.0, 170.0, 'Free WiFi, Breakfast');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('SEOUL', ARRAY['Gyeongbokgung Palace','Bukchon Hanok Village','Myeongdong'], ARRAY['Korean BBQ','Bibimbap','Kimchi'], 'Spring or Autumn') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('LAX', 'SEOUL', 'KE-12', 'Korean Air', 790.0, '12:50 AM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('SEOUL', 'Seoul Grand Hotel', 4.7, 270.0, 'Beachfront, Spa');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('SEOUL', 'Seoul Boutique Stay', 4.1, 188.0, 'Pool, Spa');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('TAIPEI', ARRAY['Taipei 101','National Palace Museum','Shilin Night Market'], ARRAY['Beef Noodle Soup','Bubble Tea','Xiaolongbao'], 'Autumn (Oct-Dec)') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('LAX', 'TAIPEI', 'CI-6', 'China Airlines', 770.0, '01:00 AM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('TAIPEI', 'Taipei Grand Hotel', 4.8, 295.0, 'Airport Shuttle, Breakfast');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('TAIPEI', 'Taipei Boutique Stay', 4.2, 206.0, 'Rooftop Bar, City View');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('HONG KONG', ARRAY['Victoria Peak','Star Ferry','Tian Tan Buddha'], ARRAY['Dim Sum','Egg Tarts','Wonton Noodles'], 'October to December') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('LAX', 'HONG KONG', 'CX-880', 'Cathay Pacific', 820.0, '01:20 AM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('HONG KONG', 'Hong Kong Grand Hotel', 4.3, 320.0, 'Free WiFi, Breakfast');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('HONG KONG', 'Hong Kong Boutique Stay', 4.3, 80.0, 'Fitness Center, Concierge');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('SYDNEY', ARRAY['Sydney Opera House','Harbour Bridge','Bondi Beach'], ARRAY['Meat Pies','Barramundi','Pavlova'], 'September to November') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('LAX', 'SYDNEY', 'QF-12', 'Qantas', 990.0, '10:40 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('SYDNEY', 'Sydney Grand Hotel', 4.4, 345.0, 'Pool, Spa');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('SYDNEY', 'Sydney Boutique Stay', 4.4, 98.0, 'Garden, Restaurant');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('AUCKLAND', ARRAY['Sky Tower','Waiheke Island','Auckland Domain'], ARRAY['Hangi','Pavlova','Green-Lipped Mussels'], 'December to February') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('LAX', 'AUCKLAND', 'NZ-6', 'Air New Zealand', 960.0, '10:15 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('AUCKLAND', 'Auckland Grand Hotel', 4.5, 120.0, 'Rooftop Bar, City View');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('AUCKLAND', 'Auckland Boutique Stay', 4.0, 116.0, 'Historic Building, Concierge');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('NADI', ARRAY['Sabeto Hot Springs','Garden of the Sleeping Giant','Denarau Island'], ARRAY['Kokoda','Lovo','Cassava'], 'May to October') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('LAX', 'NADI', 'FJ-810', 'Fiji Airways', 850.0, '09:55 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('NADI', 'Nadi Grand Hotel', 4.6, 145.0, 'Fitness Center, Concierge');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('NADI', 'Nadi Boutique Stay', 4.1, 134.0, 'Beachfront, Spa');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('TORONTO', ARRAY['CN Tower','Royal Ontario Museum','Distillery District'], ARRAY['Poutine','Butter Tarts','Peameal Bacon Sandwich'], 'Summer (June-September)') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('ORD', 'TORONTO', 'AC-621', 'Air Canada', 260.0, '07:30 AM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('TORONTO', 'Toronto Grand Hotel', 4.7, 170.0, 'Garden, Restaurant');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('TORONTO', 'Toronto Boutique Stay', 4.2, 152.0, 'Airport Shuttle, Breakfast');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('MEXICO CITY', ARRAY['Zocalo','Frida Kahlo Museum','Chapultepec Castle'], ARRAY['Tacos','Mole','Chiles en Nogada'], 'March to May') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('MIA', 'MEXICO CITY', 'AM-405', 'Aeromexico', 340.0, '08:15 AM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('MEXICO CITY', 'Mexico City Grand Hotel', 4.8, 195.0, 'Historic Building, Concierge');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('MEXICO CITY', 'Mexico City Boutique Stay', 4.3, 170.0, 'Free WiFi, Breakfast');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('HAVANA', ARRAY['Old Havana','Malecon','El Capitolio'], ARRAY['Ropa Vieja','Cuban Sandwich','Mojitos'], 'November to April') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('MIA', 'HAVANA', 'AA-987', 'American Airlines', 260.0, '09:00 AM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('HAVANA', 'Havana Grand Hotel', 4.3, 220.0, 'Beachfront, Spa');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('HAVANA', 'Havana Boutique Stay', 4.4, 188.0, 'Pool, Spa');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('MONTEGO BAY', ARRAY['Doctor''s Cave Beach','Rose Hall Great House','Blue Mountains'], ARRAY['Jerk Chicken','Ackee and Saltfish','Jamaican Patties'], 'December to April') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('MIA', 'MONTEGO BAY', 'AA-1265', 'American Airlines', 280.0, '10:30 AM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('MONTEGO BAY', 'Montego Bay Grand Hotel', 4.4, 245.0, 'Airport Shuttle, Breakfast');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('MONTEGO BAY', 'Montego Bay Boutique Stay', 4.0, 206.0, 'Rooftop Bar, City View');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('NASSAU', ARRAY['Cable Beach','Queen''s Staircase','Atlantis Paradise Island'], ARRAY['Conch Salad','Guava Duff','Johnny Cake'], 'December to April') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('MIA', 'NASSAU', 'AA-1655', 'American Airlines', 220.0, '11:00 AM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('NASSAU', 'Nassau Grand Hotel', 4.5, 270.0, 'Free WiFi, Breakfast');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('NASSAU', 'Nassau Boutique Stay', 4.1, 80.0, 'Fitness Center, Concierge');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('RIO DE JANEIRO', ARRAY['Christ the Redeemer','Copacabana Beach','Sugarloaf Mountain'], ARRAY['Feijoada','Pao de Queijo','Brigadeiro'], 'December to March') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('MIA', 'RIO DE JANEIRO', 'LA-8090', 'LATAM Airlines', 610.0, '09:20 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('RIO DE JANEIRO', 'Rio De Janeiro Grand Hotel', 4.6, 295.0, 'Pool, Spa');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('RIO DE JANEIRO', 'Rio De Janeiro Boutique Stay', 4.2, 98.0, 'Garden, Restaurant');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('BUENOS AIRES', ARRAY['La Boca','Recoleta Cemetery','Teatro Colon'], ARRAY['Asado','Empanadas','Dulce de Leche'], 'September to November') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('MIA', 'BUENOS AIRES', 'AR-1303', 'Aerolineas Argentinas', 640.0, '10:00 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('BUENOS AIRES', 'Buenos Aires Grand Hotel', 4.7, 320.0, 'Rooftop Bar, City View');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('BUENOS AIRES', 'Buenos Aires Boutique Stay', 4.3, 116.0, 'Historic Building, Concierge');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('SANTIAGO', ARRAY['Cerro San Cristobal','La Moneda Palace','Bellavista'], ARRAY['Empanadas','Curanto','Pastel de Choclo'], 'September to November') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('MIA', 'SANTIAGO', 'LA-505', 'LATAM Airlines', 630.0, '09:40 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('SANTIAGO', 'Santiago Grand Hotel', 4.8, 345.0, 'Fitness Center, Concierge');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('SANTIAGO', 'Santiago Boutique Stay', 4.4, 134.0, 'Beachfront, Spa');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('CUSCO', ARRAY['Machu Picchu','Sacsayhuaman','Plaza de Armas'], ARRAY['Ceviche','Lomo Saltado','Cuy'], 'May to September') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('MIA', 'CUSCO', 'LA-2450', 'LATAM Airlines', 590.0, '08:50 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('CUSCO', 'Cusco Grand Hotel', 4.3, 120.0, 'Garden, Restaurant');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('CUSCO', 'Cusco Boutique Stay', 4.0, 152.0, 'Airport Shuttle, Breakfast');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('CARTAGENA', ARRAY['Walled City','Castillo San Felipe','Getsemani'], ARRAY['Arepas','Ceviche','Bandeja Paisa'], 'December to April') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('MIA', 'CARTAGENA', 'AV-244', 'Avianca', 340.0, '11:20 AM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('CARTAGENA', 'Cartagena Grand Hotel', 4.4, 145.0, 'Historic Building, Concierge');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('CARTAGENA', 'Cartagena Boutique Stay', 4.1, 170.0, 'Free WiFi, Breakfast');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('QUITO', ARRAY['Historic Centre','TelefeliQo Cable Car','La Compania Church'], ARRAY['Locro de Papa','Ceviche','Empanadas'], 'June to September') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('MIA', 'QUITO', 'AV-70', 'Avianca', 420.0, '12:10 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('QUITO', 'Quito Grand Hotel', 4.5, 170.0, 'Beachfront, Spa');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('QUITO', 'Quito Boutique Stay', 4.2, 188.0, 'Pool, Spa');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('LA PAZ', ARRAY['Valle de la Luna','Witches'' Market','Mi Teleferico'], ARRAY['Saltenas','Pique Macho','Chuno'], 'May to October') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('MIA', 'LA PAZ', 'AV-84', 'Avianca', 450.0, '12:40 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('LA PAZ', 'La Paz Grand Hotel', 4.6, 195.0, 'Airport Shuttle, Breakfast');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('LA PAZ', 'La Paz Boutique Stay', 4.3, 206.0, 'Rooftop Bar, City View');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('MONTEVIDEO', ARRAY['Ciudad Vieja','Rambla','Mercado del Puerto'], ARRAY['Asado','Chivito','Dulce de Leche'], 'December to March') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('MIA', 'MONTEVIDEO', 'LA-509', 'LATAM Airlines', 620.0, '09:10 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('MONTEVIDEO', 'Montevideo Grand Hotel', 4.7, 220.0, 'Free WiFi, Breakfast');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('MONTEVIDEO', 'Montevideo Boutique Stay', 4.4, 80.0, 'Fitness Center, Concierge');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('SAN JOSE', ARRAY['Poas Volcano','National Theatre','Central Market'], ARRAY['Gallo Pinto','Casado','Ceviche'], 'December to April') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('MIA', 'SAN JOSE', 'AA-2103', 'American Airlines', 290.0, '01:15 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('SAN JOSE', 'San Jose Grand Hotel', 4.8, 245.0, 'Pool, Spa');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('SAN JOSE', 'San Jose Boutique Stay', 4.0, 98.0, 'Garden, Restaurant');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('PANAMA CITY', ARRAY['Panama Canal','Casco Viejo','Biomuseo'], ARRAY['Sancocho','Ceviche','Patacones'], 'December to April') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('MIA', 'PANAMA CITY', 'CM-201', 'Copa Airlines', 300.0, '01:45 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('PANAMA CITY', 'Panama City Grand Hotel', 4.3, 270.0, 'Rooftop Bar, City View');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('PANAMA CITY', 'Panama City Boutique Stay', 4.1, 116.0, 'Historic Building, Concierge');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('DUBROVNIK', ARRAY['City Walls','Old Town','Lokrum Island'], ARRAY['Peka','Black Risotto','Rozata'], 'May to September') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'DUBROVNIK', 'OU-460', 'Croatia Airlines', 620.0, '07:00 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('DUBROVNIK', 'Dubrovnik Grand Hotel', 4.4, 295.0, 'Fitness Center, Concierge');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('DUBROVNIK', 'Dubrovnik Boutique Stay', 4.2, 134.0, 'Beachfront, Spa');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('LJUBLJANA', ARRAY['Ljubljana Castle','Triple Bridge','Lake Bled (nearby)'], ARRAY['Potica','Kranjska Klobasa','Struklji'], 'Late Spring to Early Autumn') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'LJUBLJANA', 'LH-410', 'Lufthansa (via Munich)', 610.0, '06:50 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('LJUBLJANA', 'Ljubljana Grand Hotel', 4.5, 320.0, 'Garden, Restaurant');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('LJUBLJANA', 'Ljubljana Boutique Stay', 4.3, 152.0, 'Airport Shuttle, Breakfast');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('BUCHAREST', ARRAY['Palace of Parliament','Old Town Lipscani','Village Museum'], ARRAY['Sarmale','Mici','Papanasi'], 'May to September') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'BUCHAREST', 'RO-16', 'TAROM', 550.0, '10:00 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('BUCHAREST', 'Bucharest Grand Hotel', 4.6, 345.0, 'Historic Building, Concierge');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('BUCHAREST', 'Bucharest Boutique Stay', 4.4, 170.0, 'Free WiFi, Breakfast');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('SOFIA', ARRAY['Alexander Nevsky Cathedral','Vitosha Mountain','Boyana Church'], ARRAY['Banitsa','Shopska Salad','Kavarma'], 'May to September') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'SOFIA', 'LH-406', 'Lufthansa (via Frankfurt)', 590.0, '06:30 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('SOFIA', 'Sofia Grand Hotel', 4.7, 120.0, 'Beachfront, Spa');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('SOFIA', 'Sofia Boutique Stay', 4.0, 188.0, 'Pool, Spa');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('BELGRADE', ARRAY['Kalemegdan Fortress','Skadarlija','St. Sava Temple'], ARRAY['Cevapi','Pljeskavica','Rakija'], 'Late Spring to Early Autumn') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'BELGRADE', 'JU-501', 'Air Serbia', 570.0, '09:35 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('BELGRADE', 'Belgrade Grand Hotel', 4.8, 145.0, 'Airport Shuttle, Breakfast');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('BELGRADE', 'Belgrade Boutique Stay', 4.1, 206.0, 'Rooftop Bar, City View');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('KYIV', ARRAY['Saint Sophia Cathedral','Maidan Square','Pechersk Lavra'], ARRAY['Borscht','Varenyky','Chicken Kyiv'], 'Late Spring to Early Autumn') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'KYIV', 'LO-27', 'LOT Polish Airlines (via Warsaw)', 640.0, '07:55 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('KYIV', 'Kyiv Grand Hotel', 4.3, 170.0, 'Free WiFi, Breakfast');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('KYIV', 'Kyiv Boutique Stay', 4.2, 80.0, 'Fitness Center, Concierge');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('TBILISI', ARRAY['Old Town Tbilisi','Narikala Fortress','Abanotubani Sulphur Baths'], ARRAY['Khachapuri','Khinkali','Georgian Wine'], 'Spring or Autumn') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'TBILISI', 'TK-4', 'Turkish Airlines (via Istanbul)', 660.0, '11:15 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('TBILISI', 'Tbilisi Grand Hotel', 4.4, 195.0, 'Pool, Spa');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('TBILISI', 'Tbilisi Boutique Stay', 4.3, 98.0, 'Garden, Restaurant');
INSERT INTO destinations (city, sights, food, best_season) VALUES ('VALLETTA', ARRAY['St. John''s Co-Cathedral','Upper Barrakka Gardens','Grand Harbour'], ARRAY['Pastizzi','Rabbit Stew','Ftira'], 'Spring or Autumn') ON CONFLICT (city) DO NOTHING;
INSERT INTO flights (origin, destination, flight_no, airline, price, departure_time) VALUES ('JFK', 'VALLETTA', 'AZ-609', 'ITA Airways (via Rome)', 630.0, '10:05 PM');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('VALLETTA', 'Valletta Grand Hotel', 4.5, 220.0, 'Rooftop Bar, City View');
INSERT INTO hotels (city, name, rating, price_per_night, amenities) VALUES ('VALLETTA', 'Valletta Boutique Stay', 4.4, 116.0, 'Historic Building, Concierge');

-- Backfill country for every destination above (all INSERTs before this
-- point deliberately omit it), then lock the column NOT NULL now that every
-- row genuinely has a value - see the comment on destinations.country.
UPDATE destinations d SET country = v.country FROM (VALUES
    ('AMMAN', 'Jordan'), ('AMSTERDAM', 'Netherlands'), ('ATHENS', 'Greece'), ('AUCKLAND', 'New Zealand'),
    ('BALI', 'Indonesia'), ('BANGKOK', 'Thailand'), ('BARCELONA', 'Spain'), ('BEIJING', 'China'),
    ('BELGRADE', 'Serbia'), ('BERLIN', 'Germany'), ('BRUSSELS', 'Belgium'), ('BUCHAREST', 'Romania'),
    ('BUDAPEST', 'Hungary'), ('BUENOS AIRES', 'Argentina'), ('CAIRO', 'Egypt'), ('CAPE TOWN', 'South Africa'),
    ('CARTAGENA', 'Colombia'), ('COLOMBO', 'Sri Lanka'), ('COPENHAGEN', 'Denmark'), ('CUSCO', 'Peru'),
    ('DELHI', 'India'), ('DOHA', 'Qatar'), ('DUBAI', 'United Arab Emirates'), ('DUBLIN', 'Ireland'),
    ('DUBROVNIK', 'Croatia'), ('HANOI', 'Vietnam'), ('HAVANA', 'Cuba'), ('HELSINKI', 'Finland'),
    ('HONG KONG', 'China'), ('ISTANBUL', 'Turkey'), ('JERUSALEM', 'Israel'), ('KATHMANDU', 'Nepal'),
    ('KUALA LUMPUR', 'Malaysia'), ('KYIV', 'Ukraine'), ('KYOTO', 'Japan'), ('LA PAZ', 'Bolivia'),
    ('LAGOS', 'Nigeria'), ('LISBON', 'Portugal'), ('LJUBLJANA', 'Slovenia'), ('LONDON', 'United Kingdom'),
    ('LUANG PRABANG', 'Laos'), ('MANILA', 'Philippines'), ('MARRAKESH', 'Morocco'), ('MEXICO CITY', 'Mexico'),
    ('MONTEGO BAY', 'Jamaica'), ('MONTEVIDEO', 'Uruguay'), ('MOSCOW', 'Russia'), ('NADI', 'Fiji'),
    ('NAIROBI', 'Kenya'), ('NASSAU', 'Bahamas'), ('NEW YORK', 'United States'), ('OSLO', 'Norway'),
    ('PANAMA CITY', 'Panama'), ('PARIS', 'France'), ('PRAGUE', 'Czech Republic'), ('QUITO', 'Ecuador'),
    ('REYKJAVIK', 'Iceland'), ('RIO DE JANEIRO', 'Brazil'), ('RIYADH', 'Saudi Arabia'), ('ROME', 'Italy'),
    ('SAN JOSE', 'Costa Rica'), ('SANTIAGO', 'Chile'), ('SEOUL', 'South Korea'), ('SIEM REAP', 'Cambodia'),
    ('SINGAPORE', 'Singapore'), ('SOFIA', 'Bulgaria'), ('STOCKHOLM', 'Sweden'), ('SYDNEY', 'Australia'),
    ('TAIPEI', 'Taiwan'), ('TBILISI', 'Georgia'), ('TOKYO', 'Japan'), ('TORONTO', 'Canada'),
    ('VALLETTA', 'Malta'), ('VANCOUVER', 'Canada'), ('VIENNA', 'Austria'), ('WARSAW', 'Poland'),
    ('YANGON', 'Myanmar'), ('ZANZIBAR', 'Tanzania'), ('ZURICH', 'Switzerland')
) AS v(city, country)
WHERE d.city = v.city;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM destinations WHERE country IS NULL) THEN
        RAISE EXCEPTION 'destinations has row(s) with no country - add the new city to the mapping above';
    END IF;
END $$;

ALTER TABLE destinations ALTER COLUMN country SET NOT NULL;
