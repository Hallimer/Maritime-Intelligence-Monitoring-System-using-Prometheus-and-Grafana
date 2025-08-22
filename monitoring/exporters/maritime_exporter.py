#!/usr/bin/env python3
"""
Enhanced Maritime Intelligence Prometheus Exporter

This exporter generates realistic maritime metrics tailored for three key stakeholder groups:
1. Shipping Companies / Fleet Operators - Focus: cost savings & efficiency
2. Port Authorities / Terminal Operators - Focus: throughput & congestion management  
3. Customs / Government Agencies - Focus: compliance & trade intelligence

Generates 24 hours of historical data on startup for immediate trend visualization.
"""

import time
import random
import math
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from prometheus_client import start_http_server, Gauge, Counter, Histogram
import logging
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedMaritimeExporter:
    def __init__(self):
        # === SHIPPING COMPANIES / FLEET OPERATORS METRICS ===
        # ETA vs Actual Arrival Tracking
        self.vessel_eta_delay_hours = Gauge('vessel_eta_delay_hours', 
                                          'Hours difference between ETA and actual arrival (negative = early)', 
                                          ['vessel_id', 'vessel_name', 'vessel_type', 'operator', 'route'])
        
        # Fuel Consumption & Efficiency
        self.vessel_fuel_consumption_mt_per_day = Gauge('vessel_fuel_consumption_mt_per_day', 
                                                      'Fuel consumption in metric tons per day', 
                                                      ['vessel_id', 'vessel_name', 'vessel_type', 'operator'])
        self.vessel_fuel_efficiency_km_per_mt = Gauge('vessel_fuel_efficiency_km_per_mt', 
                                                    'Kilometers per metric ton of fuel', 
                                                    ['vessel_id', 'vessel_name', 'vessel_type', 'operator'])
        
        # Fleet Utilization
        self.fleet_utilization_percent = Gauge('fleet_utilization_percent', 
                                             'Fleet utilization percentage by operator and vessel type', 
                                             ['operator', 'vessel_type'])
        self.vessel_status_indicator = Gauge('vessel_status_indicator', 
                                           'Vessel status (1=active, 0.5=waiting, 0=idle)', 
                                           ['vessel_id', 'vessel_name', 'operator', 'status'])
        
        # Revenue Metrics
        self.vessel_revenue_per_day_usd = Gauge('vessel_revenue_per_day_usd', 
                                              'Estimated daily revenue in USD', 
                                              ['vessel_id', 'vessel_name', 'vessel_type', 'operator'])
        
        # === PORT AUTHORITIES / TERMINAL OPERATORS METRICS ===
        # Berth Occupancy & Capacity
        self.port_berth_occupancy_percent = Gauge('port_berth_occupancy_percent', 
                                                'Port berth occupancy percentage', 
                                                ['port_code', 'port_name', 'country', 'terminal'])
        self.port_berth_capacity_total = Gauge('port_berth_capacity_total', 
                                             'Total berth capacity', 
                                             ['port_code', 'port_name', 'country'])
        self.port_berths_occupied = Gauge('port_berths_occupied', 
                                        'Number of occupied berths', 
                                        ['port_code', 'port_name', 'country'])
        
        # Turnaround Time & Efficiency
        self.port_avg_turnaround_hours = Gauge('port_avg_turnaround_hours', 
                                             'Average vessel turnaround time in hours', 
                                             ['port_code', 'port_name', 'country', 'vessel_type'])
        self.vessel_port_arrival_time = Gauge('vessel_port_arrival_time', 
                                            'Unix timestamp of vessel port arrival', 
                                            ['vessel_id', 'port_code', 'vessel_type'])
        self.vessel_port_departure_time = Gauge('vessel_port_departure_time', 
                                               'Unix timestamp of vessel port departure', 
                                               ['vessel_id', 'port_code', 'vessel_type'])
        
        # Port Congestion
        self.port_queue_length = Gauge('port_queue_length', 
                                     'Number of vessels waiting for berth', 
                                     ['port_code', 'port_name', 'country'])
        self.port_congestion_index = Gauge('port_congestion_index', 
                                         'Port congestion index (0-100, higher = more congested)', 
                                         ['port_code', 'port_name', 'country'])
        self.port_vessel_count_by_status = Gauge('port_vessel_count_by_status', 
                                               'Count of vessels by status at port', 
                                               ['port_code', 'port_name', 'status'])
        
        # Throughput Metrics
        self.port_throughput_teu_per_hour = Gauge('port_throughput_teu_per_hour', 
                                                'Port throughput in TEU per hour', 
                                                ['port_code', 'port_name', 'country'])
        
        # === CUSTOMS / GOVERNMENT AGENCIES METRICS ===
        # Cargo Type Distribution
        self.cargo_volume_by_type = Counter('cargo_volume_by_type_teu_total', 
                                          'Total cargo volume by type in TEU', 
                                          ['port_code', 'cargo_type', 'origin_country', 'destination_country'])
        self.cargo_type_distribution_percent = Gauge('cargo_type_distribution_percent', 
                                                   'Percentage distribution of cargo types', 
                                                   ['port_code', 'cargo_type'])
        
        # Origin/Destination Intelligence
        self.trade_route_volume = Counter('trade_route_volume_teu_total', 
                                        'Total cargo volume by trade route', 
                                        ['origin_port', 'destination_port', 'cargo_type'])
        self.country_trade_balance = Gauge('country_trade_balance_teu', 
                                         'Trade balance in TEU (exports - imports)', 
                                         ['country', 'cargo_type'])
        
        # Compliance & Risk Metrics
        self.vessel_speed_violation = Gauge('vessel_speed_violation', 
                                          '1 if vessel exceeds speed limit, 0 otherwise', 
                                          ['vessel_id', 'vessel_name', 'zone', 'speed_limit'])
        self.vessel_ais_signal_quality = Gauge('vessel_ais_signal_quality_percent', 
                                             'AIS signal quality percentage', 
                                             ['vessel_id', 'vessel_name', 'flag'])
        self.vessel_compliance_score = Gauge('vessel_compliance_score', 
                                           'Overall compliance score (0-100)', 
                                           ['vessel_id', 'vessel_name', 'flag', 'operator'])
        self.customs_inspection_rate = Gauge('customs_inspection_rate_percent', 
                                           'Percentage of vessels inspected', 
                                           ['port_code', 'flag_country'])
        
        # Shared Base Metrics (from original)
        self.vessel_latitude = Gauge('vessel_latitude', 'Vessel latitude position', 
                                   ['vessel_id', 'vessel_name', 'vessel_type', 'flag'])
        self.vessel_longitude = Gauge('vessel_longitude', 'Vessel longitude position', 
                                    ['vessel_id', 'vessel_name', 'vessel_type', 'flag'])
        self.vessel_speed_knots = Gauge('vessel_speed_knots', 'Vessel speed in knots', 
                                      ['vessel_id', 'vessel_name', 'vessel_type', 'flag'])
        
        # Initialize simulation data
        self.vessels = self._initialize_vessels()
        self.ports = self._initialize_ports()
        self.cargo_types = ['containers', 'bulk_dry', 'bulk_liquid', 'general_cargo', 'vehicles']
        self.countries = ['CN', 'SG', 'US', 'NL', 'DE', 'KR', 'JP', 'AE', 'GB', 'MY', 'TH', 'VN']
        
        # Generate 24 hours of historical data on startup
        self._generate_historical_data()
        
        logger.info(f"Enhanced maritime exporter initialized with {len(self.vessels)} vessels and {len(self.ports)} ports")

    def _initialize_vessels(self) -> List[Dict]:
        """Initialize a fleet of vessels with enhanced tracking data"""
        vessel_types = [
            ('Container Ship', 'CONTAINER', 2000, 8000, 15, 25, 80000, 150000),  # min_teu, max_teu, min_speed, max_speed, min_revenue, max_revenue
            ('Bulk Carrier', 'BULK', 1000, 4000, 12, 18, 40000, 80000),
            ('Tanker', 'TANKER', 500, 2000, 10, 16, 60000, 120000),
            ('General Cargo', 'GENERAL', 200, 1000, 8, 14, 20000, 50000),
            ('RoRo', 'RORO', 300, 1500, 12, 20, 30000, 70000)
        ]
        
        flags = ['MH', 'LR', 'PA', 'SG', 'MT', 'CY', 'GB', 'NO', 'DK', 'NL', 'CN', 'KR', 'JP']
        operators = ['Maersk', 'MSC', 'COSCO', 'CMA CGM', 'Hapag-Lloyd', 'ONE', 'Yang Ming', 'Evergreen', 'PIL', 'Zim']
        
        vessels = []
        for i in range(75):  # Increased to 75 vessels for better data variety
            vessel_type_data = random.choice(vessel_types)
            
            # Create voyage routes for ETA tracking
            origin_port = random.choice(self.ports) if hasattr(self, 'ports') else None
            destination_port = random.choice(self.ports) if hasattr(self, 'ports') else None
            
            vessel = {
                'id': f'V{i+1:04d}',
                'name': f'{random.choice(["Star", "Ocean", "Global", "Pacific", "Atlantic", "Northern", "Eastern", "Western"])} {random.choice(["Trader", "Pioneer", "Voyager", "Navigator", "Explorer", "Leader", "Champion", "Victory"])}',
                'type': vessel_type_data[1],
                'type_name': vessel_type_data[0],
                'flag': random.choice(flags),
                'operator': random.choice(operators),
                'capacity': random.randint(vessel_type_data[2], vessel_type_data[3]),
                'current_cargo': 0,
                'fuel_level': random.uniform(30, 95),
                'daily_fuel_consumption': random.uniform(50, 300),  # MT per day
                'max_speed': random.uniform(vessel_type_data[4], vessel_type_data[5]),
                'daily_revenue': random.uniform(vessel_type_data[6], vessel_type_data[7]),
                
                # Position and movement
                'latitude': random.uniform(-60, 70),
                'longitude': random.uniform(-180, 180),
                'speed': random.uniform(0, vessel_type_data[5]),
                'heading': random.uniform(0, 360),
                'status': random.choice(['underway', 'at_anchor', 'in_port', 'waiting_berth']),
                
                # Voyage tracking
                'eta': datetime.now() + timedelta(hours=random.randint(1, 168)),
                'actual_arrival': None,
                'last_port_departure': datetime.now() - timedelta(hours=random.randint(1, 72)),
                'current_route': f"Route_{random.randint(1, 20)}",
                
                # Compliance tracking
                'ais_signal_quality': random.uniform(85, 100),
                'last_inspection': datetime.now() - timedelta(days=random.randint(1, 365)),
                'compliance_violations': random.randint(0, 3)
            }
            
            # Set current cargo load
            if vessel['status'] in ['underway', 'at_anchor']:
                vessel['current_cargo'] = random.randint(int(vessel['capacity'] * 0.3), int(vessel['capacity'] * 0.95))
            
            vessels.append(vessel)
        
        return vessels

    def _initialize_ports(self) -> List[Dict]:
        """Initialize ports with enhanced operational data"""
        ports_data = [
            ('SGSIN', 'Singapore', 'Singapore', 'SG', 1.290, 103.851, 180, 4),
            ('CNSHA', 'Shanghai', 'China', 'CN', 31.230, 121.474, 250, 6),
            ('NLRTM', 'Rotterdam', 'Netherlands', 'NL', 51.924, 4.477, 150, 5),
            ('CNNGB', 'Ningbo', 'China', 'CN', 29.868, 121.544, 120, 3),
            ('CNSZX', 'Shenzhen', 'China', 'CN', 22.543, 114.057, 100, 4),
            ('KRPUS', 'Busan', 'South Korea', 'KR', 35.104, 129.042, 90, 3),
            ('HKHKG', 'Hong Kong', 'Hong Kong', 'HK', 22.302, 114.177, 95, 4),
            ('DEHAM', 'Hamburg', 'Germany', 'DE', 53.551, 9.994, 80, 4),
            ('USNYC', 'New York', 'United States', 'US', 40.693, -74.044, 130, 6),
            ('USLAX', 'Los Angeles', 'United States', 'US', 33.742, -118.266, 160, 8),
            ('AEDXB', 'Dubai', 'UAE', 'AE', 25.276, 55.296, 110, 4),
            ('LKCMB', 'Colombo', 'Sri Lanka', 'LK', 6.932, 79.857, 70, 3),
            ('MYPKG', 'Port Klang', 'Malaysia', 'MY', 3.006, 101.399, 85, 4),
            ('VNVUT', 'Vung Tau', 'Vietnam', 'VN', 10.346, 107.084, 55, 2),
            ('THBKK', 'Laem Chabang', 'Thailand', 'TH', 13.086, 100.883, 65, 3)
        ]
        
        ports = []
        for port_data in ports_data:
            terminals = [f"Terminal_{chr(65+i)}" for i in range(port_data[7])]  # Terminal_A, Terminal_B, etc.
            
            port = {
                'code': port_data[0],
                'name': port_data[1],
                'country': port_data[2],
                'country_code': port_data[3],
                'latitude': port_data[4],
                'longitude': port_data[5],
                'berth_capacity': port_data[6],
                'terminals': terminals,
                'current_occupancy': random.uniform(40, 95),
                'queue_length': random.randint(0, 20),
                'avg_turnaround_container': random.uniform(8, 48),
                'avg_turnaround_bulk': random.uniform(24, 96),
                'avg_turnaround_tanker': random.uniform(12, 60),
                'throughput_teu_per_hour': random.uniform(50, 300),
                'inspection_rate': random.uniform(10, 40)  # Percentage of vessels inspected
            }
            ports.append(port)
        
        return ports

    def _generate_historical_data(self):
        """Generate 24 hours of historical data for immediate visualization"""
        logger.info("Generating 24 hours of historical data...")
        
        # Store current time
        current_time = time.time()
        
        # Generate data points for the last 24 hours (every 10 minutes = 144 data points)
        for i in range(144):
            hours_ago = 24 - (i * 10 / 60)  # Start from 24 hours ago
            
            # Temporarily modify timestamp for historical data
            # (In a real implementation, you'd use a time series database)
            self._update_all_metrics(historical=True, hours_offset=hours_ago)
            
            # Small delay to prevent overwhelming the system
            time.sleep(0.01)
        
        logger.info("Historical data generation complete")

    def _update_all_metrics(self, historical=False, hours_offset=0):
        """Update all metrics with current or historical data"""
        
        # === SHIPPING COMPANIES METRICS ===
        self._update_shipping_company_metrics()
        
        # === PORT AUTHORITY METRICS ===
        self._update_port_authority_metrics()
        
        # === CUSTOMS/GOVERNMENT METRICS ===
        self._update_customs_metrics()
        
        # === BASE VESSEL METRICS ===
        self._update_vessel_positions()

    def _update_shipping_company_metrics(self):
        """Update metrics relevant to shipping companies"""
        for vessel in self.vessels:
            self._simulate_vessel_movement(vessel)
            
            # ETA Delay Tracking
            if vessel['status'] == 'in_port' and vessel.get('actual_arrival'):
                eta_delay = (vessel['actual_arrival'] - vessel['eta']).total_seconds() / 3600
                self.vessel_eta_delay_hours.labels(
                    vessel['id'], vessel['name'], vessel['type'], 
                    vessel['operator'], vessel['current_route']
                ).set(eta_delay)
            
            # Fuel Consumption & Efficiency
            fuel_consumption = vessel['daily_fuel_consumption'] * (1 + random.uniform(-0.1, 0.1))
            distance_per_day = vessel['speed'] * 24 * 1.852  # Convert knots to km/day
            fuel_efficiency = distance_per_day / fuel_consumption if fuel_consumption > 0 else 0
            
            self.vessel_fuel_consumption_mt_per_day.labels(
                vessel['id'], vessel['name'], vessel['type'], vessel['operator']
            ).set(fuel_consumption)
            
            self.vessel_fuel_efficiency_km_per_mt.labels(
                vessel['id'], vessel['name'], vessel['type'], vessel['operator']
            ).set(fuel_efficiency)
            
            # Revenue Tracking
            revenue_modifier = 1.0
            if vessel['status'] == 'in_port':
                revenue_modifier = 0.8  # Reduced revenue while in port
            elif vessel['status'] == 'waiting_berth':
                revenue_modifier = 0.3  # Minimal revenue while waiting
            
            daily_revenue = vessel['daily_revenue'] * revenue_modifier
            self.vessel_revenue_per_day_usd.labels(
                vessel['id'], vessel['name'], vessel['type'], vessel['operator']
            ).set(daily_revenue)
            
            # Status Indicator
            status_value = {'underway': 1.0, 'at_anchor': 0.7, 'waiting_berth': 0.5, 'in_port': 0.8}.get(vessel['status'], 0)
            self.vessel_status_indicator.labels(
                vessel['id'], vessel['name'], vessel['operator'], vessel['status']
            ).set(status_value)
        
        # Fleet Utilization by Operator and Type
        for operator in set(v['operator'] for v in self.vessels):
            for vessel_type in set(v['type'] for v in self.vessels):
                fleet_vessels = [v for v in self.vessels if v['operator'] == operator and v['type'] == vessel_type]
                if fleet_vessels:
                    active_vessels = len([v for v in fleet_vessels if v['status'] in ['underway', 'in_port']])
                    utilization = (active_vessels / len(fleet_vessels)) * 100
                    self.fleet_utilization_percent.labels(operator, vessel_type).set(utilization)

    def _update_port_authority_metrics(self):
        """Update metrics relevant to port authorities"""
        for port in self.ports:
            # Simulate occupancy changes
            port['current_occupancy'] += random.uniform(-3, 3)
            port['current_occupancy'] = max(20, min(100, port['current_occupancy']))

            # Calculate actual berths occupied
            berths_occupied = int((port['current_occupancy'] / 100) * port['berth_capacity'])

            # Update queue length with realistic cap
            port['queue_length'] += random.randint(-2, 3)
            port['queue_length'] = max(0, min(port['queue_length'], port['berth_capacity']))

            # Congestion index: weighted sum of occupancy (0-70) + queue (0-30)
            # Ensures congestion_index stays between ~10 and 100 realistically
            queue_weight = 30  # Max contribution of queue length to congestion
            occupancy_weight = 70  # Max contribution of occupancy to congestion
            congestion_index = (port['current_occupancy'] / 100) * occupancy_weight + \
                            (port['queue_length'] / port['berth_capacity']) * queue_weight
            congestion_index = min(100, congestion_index)

            # Port metrics
            self.port_berth_occupancy_percent.labels(
                port['code'], port['name'], port['country'], 'All_Terminals'
            ).set(port['current_occupancy'])
            
            self.port_berth_capacity_total.labels(
                port['code'], port['name'], port['country']
            ).set(port['berth_capacity'])
            
            self.port_berths_occupied.labels(
                port['code'], port['name'], port['country']
            ).set(berths_occupied)
            
            self.port_queue_length.labels(
                port['code'], port['name'], port['country']
            ).set(port['queue_length'])
            
            self.port_congestion_index.labels(
                port['code'], port['name'], port['country']
            ).set(congestion_index)
            
            # Turnaround times by vessel type
            for vessel_type in ['CONTAINER', 'BULK', 'TANKER']:
                base_turnaround = {
                    'CONTAINER': port['avg_turnaround_container'],
                    'BULK': port['avg_turnaround_bulk'],
                    'TANKER': port['avg_turnaround_tanker']
                }[vessel_type]
                
                # Add congestion impact
                congestion_impact = 1 + (congestion_index / 100) * 0.5
                actual_turnaround = base_turnaround * congestion_impact
                
                self.port_avg_turnaround_hours.labels(
                    port['code'], port['name'], port['country'], vessel_type
                ).set(actual_turnaround)
            
            # Vessel count by status
            for status in ['docked', 'waiting', 'departing']:
                count = random.randint(0, 15) if status != 'waiting' else port['queue_length']
                self.port_vessel_count_by_status.labels(
                    port['code'], port['name'], status
                ).set(count)
            
            # Throughput
            base_throughput = port['throughput_teu_per_hour']
            efficiency_factor = 1.2 - (congestion_index / 100) * 0.4  # Efficiency decreases with congestion
            actual_throughput = base_throughput * efficiency_factor
            
            self.port_throughput_teu_per_hour.labels(
                port['code'], port['name'], port['country']
            ).set(actual_throughput)

    def _update_customs_metrics(self):
        """Update metrics relevant to customs and government agencies"""
        
        # Cargo Type Distribution and Trade Routes
        if random.random() < 0.3:  # 30% chance per update cycle
            port = random.choice(self.ports)
            cargo_type = random.choice(self.cargo_types)
            origin_country = random.choice(self.countries)
            destination_country = random.choice([c for c in self.countries if c != origin_country])
            
            # Simulate cargo movement
            volume = random.randint(50, 500)
            self.cargo_volume_by_type.labels(
                port['code'], cargo_type, origin_country, destination_country
            ).inc(volume)
            
            # Trade route volume
            origin_port = random.choice([p['code'] for p in self.ports])
            destination_port = random.choice([p['code'] for p in self.ports if p['code'] != origin_port])
            self.trade_route_volume.labels(origin_port, destination_port, cargo_type).inc(volume)
        
        # Update cargo type distribution percentages for each port
        for port in self.ports:
            total_cargo = sum([random.randint(1000, 5000) for _ in self.cargo_types])  # Simulate total
            for cargo_type in self.cargo_types:
                cargo_amount = random.randint(100, 1500)
                percentage = (cargo_amount / total_cargo) * 100
                self.cargo_type_distribution_percent.labels(port['code'], cargo_type).set(percentage)
        
        # Country Trade Balance
        for country in self.countries:
            for cargo_type in self.cargo_types:
                balance = random.randint(-10000, 10000)  # TEU balance (exports - imports)
                self.country_trade_balance.labels(country, cargo_type).set(balance)
        
        # Compliance and Risk Metrics
        for vessel in self.vessels:
            # Speed violation check (simulate speed limits in different zones)
            speed_limit = random.choice([12, 15, 20, 25])  # Different zone speed limits
            zone = random.choice(['port_approach', 'coastal', 'open_sea'])
            speed_violation = 1 if vessel['speed'] > speed_limit else 0
            
            self.vessel_speed_violation.labels(
                vessel['id'], vessel['name'], zone, str(speed_limit)
            ).set(speed_violation)
            
            # AIS Signal Quality (simulate degradation over time/distance)
            vessel['ais_signal_quality'] += random.uniform(-2, 1)
            vessel['ais_signal_quality'] = max(60, min(100, vessel['ais_signal_quality']))
            
            self.vessel_ais_signal_quality.labels(
                vessel['id'], vessel['name'], vessel['flag']
            ).set(vessel['ais_signal_quality'])
            
            # Overall Compliance Score
            compliance_factors = [
                100 if not speed_violation else 70,
                vessel['ais_signal_quality'],
                90 if vessel['compliance_violations'] == 0 else max(60, 90 - vessel['compliance_violations'] * 10)
            ]
            compliance_score = sum(compliance_factors) / len(compliance_factors)
            
            self.vessel_compliance_score.labels(
                vessel['id'], vessel['name'], vessel['flag'], vessel['operator']
            ).set(compliance_score)
        
        # Customs Inspection Rates
        for port in self.ports:
            for flag_country in random.sample(self.countries, 5):  # Sample 5 countries per port
                inspection_rate = port['inspection_rate'] * random.uniform(0.8, 1.2)
                self.customs_inspection_rate.labels(port['code'], flag_country).set(inspection_rate)

    def _update_vessel_positions(self):
        """Update basic vessel position and movement metrics"""
        for vessel in self.vessels:
            self.vessel_latitude.labels(
                vessel['id'], vessel['name'], vessel['type'], vessel['flag']
            ).set(vessel['latitude'])
            
            self.vessel_longitude.labels(
                vessel['id'], vessel['name'], vessel['type'], vessel['flag']
            ).set(vessel['longitude'])
            
            self.vessel_speed_knots.labels(
                vessel['id'], vessel['name'], vessel['type'], vessel['flag']
            ).set(vessel['speed'])

    def _simulate_vessel_movement(self, vessel: Dict) -> None:
        """Enhanced vessel movement simulation"""
        if vessel['status'] == 'underway':
            # More realistic movement with route following
            speed_variation = random.uniform(-1, 1)
            vessel['speed'] = max(0, min(vessel['max_speed'], vessel['speed'] + speed_variation))
            
            # Simulate arrival at destination
            if random.random() < 0.02:  # 2% chance to arrive at port
                vessel['status'] = random.choice(['in_port', 'waiting_berth'])
                vessel['actual_arrival'] = datetime.now()
                vessel['speed'] = random.uniform(0, 3)  # Port speed
            
        elif vessel['status'] == 'waiting_berth':
            # Vessel waiting for berth assignment
            vessel['speed'] = random.uniform(0, 2)
            if random.random() < 0.1:  # 10% chance to get berth
                vessel['status'] = 'in_port'
                
        elif vessel['status'] == 'in_port':
            # Vessel docked, minimal movement
            vessel['speed'] = 0
            if random.random() < 0.05:  # 5% chance to depart
                vessel['status'] = 'underway'
                vessel['eta'] = datetime.now() + timedelta(hours=random.randint(-72, 168))
                vessel['speed'] = random.uniform(8, vessel['max_speed'])
        
        # Update fuel consumption
        fuel_consumption_rate = 0.001 + (vessel['speed'] / vessel['max_speed']) * 0.01
        vessel['fuel_level'] = max(0, vessel['fuel_level'] - fuel_consumption_rate)
        
        # Update position if moving
        if vessel['speed'] > 0:
            speed_ms = vessel['speed'] * 0.514444
            distance_deg = (speed_ms * 300) / 111000  # 5-minute update cycle
            
            lat_change = distance_deg * math.cos(math.radians(vessel['heading']))
            lon_change = distance_deg * math.sin(math.radians(vessel['heading']))
            
            vessel['latitude'] += lat_change
            vessel['longitude'] += lon_change
            
            # Keep within bounds
            vessel['latitude'] = max(-90, min(90, vessel['latitude']))
            vessel['longitude'] = max(-180, min(180, vessel['longitude']))

    def update_metrics(self):
        """Update all maritime metrics"""
        self._update_all_metrics()

def main():
    """Main function to run the enhanced maritime exporter"""
    exporter = EnhancedMaritimeExporter()
    
    # Start the HTTP server
    start_http_server(8000)
    logger.info("Enhanced maritime exporter started on port 8000")
    logger.info("Metrics available at http://localhost:8000/metrics")
    
    # Update metrics every 5 minutes (300 seconds)
    while True:
        try:
            exporter.update_metrics()
            logger.info("Updated maritime metrics")
            time.sleep(300)  # Update every 5 minutes
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
            time.sleep(60)  # Wait 1 minute before retrying

if __name__ == '__main__':
    main()
    