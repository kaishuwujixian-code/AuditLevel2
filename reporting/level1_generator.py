import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from docx import Document
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph
import json
import os


# -------------------- Measure templates -------------------- #


MEASURE_TEMPLATES = {
    "BAS Upgrade": {
        "name": "Building Automation System Upgrade",
        "existing": (
            "The building’s mechanical systems are currently controlled by a combination of "
            "local thermostats and standalone unit controllers. There is limited central monitoring "
            "of setpoints, schedules, or alarms. Occupancy patterns have changed since the original "
            "systems were installed, and equipment is often left running at full capacity during "
            "evenings and weekends."
        ),
        "retrofit": (
            "Mann recommends upgrading to a modern Building Automation System (BAS) that integrates "
            "the boiler plant, make-up air units, pumps and exhaust fans. The BAS will provide central "
            "scheduling, outdoor-reset control, supply-air temperature reset and alarm monitoring. "
            "This will allow operators to implement unoccupied setbacks, improve temperature control "
            "and identify equipment faults more quickly.\n\n"
            "With proper programming, the BAS will optimise equipment sequencing so that the most "
            "efficient boilers and pumps are operated first, and ventilation rates can be reduced "
            "when spaces are unoccupied. This measure improves comfort, reduces natural-gas and "
            "electricity consumption, and provides a platform for future energy-saving strategies."
        ),
    },
    "Condensing Boiler Retrofit": {
        "name": "Condensing Boiler Retrofit",
        "existing": (
            "The existing heating boilers in the mechanical room are non-condensing, gas-fired LAARS units installed in 2014,"
            " with an estimated thermal efficiency of approximately 80%. As non-condensing equipment, they operate with higher"
            " flue-gas temperatures and cannot recover latent heat from combustion, resulting in reduced overall efficiency "
            "compared to modern condensing boiler technologies.\n\n"
            "The boilers also not integrate with BAS, lack advanced control features such as setpoint adjustment based "
            "on outdoor air temperature and real-time modulation optimization. This limited control capability contributes "
            "to frequent short cycling and increased natural gas consumption. As a result, the system experiences elevated "
            "utility costs and higher greenhouse gas emissions.\n\n"
            "While the boilers remain operational and continue to provide reliable heating performance, their age "
            "and conventional atmospheric design limit overall system efficiency compared to modern condensing technology. "
            "Although there is no immediate need for replacement, planning for a long-term boiler upgrade would allow the "
            "building to benefit from improved energy efficiency, reduced operating costs, and enhanced modulation and "
            "control capabilities in future years."
        ),
        "retrofit": (
            "Mann recommended that the existing non-condensing boilers be replaced with high-efficiency condensing boilers. "
            "Condensing boilers are designed to extract additional heat from the flue gases by recovering latent heat through "
            "a secondary heat exchanger, allowing them to achieve thermal efficiencies of up to 98%. This upgrade would "
            "substantially reduce natural gas consumption, lower utility costs, and improve overall system performance.\n\n"
            "Modern condensing boilers also provide advanced control capabilities, including high-turndown modulation, "
            "integrated sequencing, and seamless compatibility with Building Automation Systems (BAS). These features "
            "improve load matching, reduce equipment cycling, and enhance operational reliability.\n\n"
            "Upgrading to condensing boiler technology not only increases energy efficiency and reduces "
            "ongoing operating costs but also supports long-term sustainability objectives and contributes to meaningful "
            "reductions in greenhouse gas emissions. Piping would be reconfigured to reduce standby losses and protect the boilers from thermal shock."

        ),
    },
    "Fancoil to WSHP(short term)": {
        "name": "Water Source Heat Pump System Conversion",
        "existing": (
            "The building currently operates with a traditional two-pipe fan coil system that provides either heating or cooling "
            "depending on the season. Each suite is equipped with an original fan coil unit that receives hot water from the central "
            "boiler plant during the heating season and chilled water from the central chiller and cooling tower during the cooling season.\n\n"
            "Because the system is two-pipe, the fan coils cannot supply heating and cooling simultaneously. A full building "
            "changeover is required in the spring and fall to shift between heating and cooling modes. This limitation often "
            "results in periods of thermal discomfort during shoulder seasons, as individual suites have no ability to select heating or cooling independently.\n\n"
            "The fan coils are original to the building and have surpassed their expected service life. Aging components, "
            "reduced reliability, and declining performance contribute to inconsistent temperature control, elevated maintenance "
            "requirements, and reduced energy efficiency"
        ),
        "retrofit": (
            "Mann proposes the installation of a water source heat pump for winter and summer operation. The heat pump can "
            "be installed in the existing fan coil cabinet when the fan coils are scheduled for replacement. The existing "
            "piping can remain and be reused. The existing boiler plant can remain. The chiller is no longer required and "
            "only a fluid cooler can be installed in place of the existing cooling tower. This retrofit is ideal when the "
            "fan coils and chiller are scheduled for replacement as the incremental cost of the heat pump system compared "
            "to replacing the fan coils and chiller is marginal. The water source heat pump system is far more efficient "
            "than the existing fan coil system and is capable of heating or cooling operation at any time of the year. "
            "One consideration is the electrical supply in the suites as the heat pumps have a higher electrical demand "
            "compared to the fan coils since it consists of a compressor.\n\n "
            "As opposed to a 2-pipe fan coil system which operates at a design loop temp of 140F during heating season "
            "and 45F during cooling season, a water source heat pump system operates between 70-90F year around, meaning "
            "that the piping does not need to be insulated and there is minimal heat loss from the piping. It also means "
            "that the boiler system will always be operating in condensing temperatures with an extremely high thermal "
            "efficiency 95%+. Also, the heat input from the boiler system is greatly reduced meaning that the boiler "
            "plant can be downsized.\n\n "
            "In the heating season, the heat pumps extract heat from the hydronic loop and pump it into the suite. "
            "When more heat is required than is being generated within the building and most units are operating in "
            "heating mode, supplemental heating is supplied from a central boiler plant.\n\n "
            "In the cooling season, the heat pumps extract heat from the suites and pump it into the hydronic loop. "
            "When most of the units are in cooling mode and the heat is not needed elsewhere in the building, the "
            "heat is rejected from the loop using a fluid cooler. As opposed to a chiller, a fluid cooler comes at a "
            "much lower upfront and maintenance cost.\n\n "
            "During shoulder seasons, the system is capable of heat recycling, as heat from a suite calling for "
            "cooling such as a south elevation can transfer heat directly to another suite which is calling for "
            "heating such as a north elevation. In this case, no heat is rejected or input into the system.\n\n "
            "This measure eliminates the need for a chiller. Water source heat pump systems with fan coil units "
            "represent a sustainable and efficient HVAC solution suitable for a wide range of applications. "
            "By harnessing the thermal properties of water, these systems contribute to energy savings, environmental responsibility, and occupant comfort.\n\n "
            "*Further engineering details are required to finalize this measure.."
        ),
    },
    "Investigate Electric Heating": {
        "name": "Investigate and Eliminate Sources of Electrical Heating",
        "existing": (
            "There is a significant increase in electrical consumption during the winter season, "
            "approximately 33% higher than shoulder-season baseload consumption. This is unusual for a "
            "building heated primarily by a natural-gas boiler plant. Possible sources of electrical "
            "heating include garage ramp heating and resistive electric space heaters. These sources may "
            "be operating wastefully or without proper control."
        ),
        "retrofit": (
            "Mann recommends conducting a targeted investigation to identify and eliminate or optimise all "
            "electrical heating sources during the winter. Resistive electric heating is an extremely "
            "inefficient means of providing space heat. The investigation should include a thorough "
            "inspection of all electrical heating equipment and controls to identify malfunctions, "
            "incorrect setpoints or poor scheduling that may be contributing to increased consumption, "
            "and to develop specific solutions to reduce winter electrical heating use."
        ),
    },
}
MEASURE_TEMPLATES.update({
    "Existing BAS Upgrade": {
        "name": "Existing BAS Upgrade",
        "existing": (
            "The building’s HVAC systems operate using a mixture of local controls and a legacy "
            "building automation system (BAS) that provides limited monitoring capability. The "
            "control platform has not been comprehensively updated or recalibrated for several "
            "years, and the level of integration varies across equipment. Many components operate "
            "with minimal feedback, limited scheduling capability, and reduced visibility into "
            "equipment performance. Legacy or partially obsolete control devices are difficult to "
            "maintain, prone to failures, and may no longer be fully supported by the manufacturer."
        ),
        "retrofit": (
            "Mann recommends implementing a comprehensive BAS upgrade to provide modern, centralized "
            "control and monitoring of all major HVAC systems. The retrofit would consolidate the "
            "existing control infrastructure into a unified digital platform capable of advanced "
            "sequencing, optimized scheduling, remote monitoring, trending, and alarms. Outdated "
            "control devices would be replaced with new DDC components. A non-proprietary framework "
            "such as Niagara 4 is recommended to allow future expansion and easier maintenance. "
            "The upgraded BAS is expected to reduce energy use, improve comfort, and extend equipment "
            "service life. Enbridge Gas incentive programs for advanced building controls can help "
            "offset capital costs and improve project payback."
        ),
    },

    "Sub-metering": {
        "name": "Electrical Sub-metering",
        "existing": (
            "The building is served by a single interval meter and there is currently no electrical "
            "sub-metering system in place to monitor power distribution or track the electricity use "
            "of individual tenants or loads."
        ),
        "retrofit": (
            "It is recommended to install an electrical sub-metering system to measure electricity "
            "use by tenant or by major end-use. Certified sub-meters would be installed on the main "
            "feeds in electrical closets and programmed to track usage for each unit or load. "
            "Sub-metering enables fair, consumption-based billing and encourages occupants to reduce "
            "waste, typically resulting in 5–30% electricity savings per suite. Measurement Canada "
            "certified meters ensure accuracy and tamper resistance, making this a practical solution "
            "for existing multi-unit buildings where full utility meter replacement is not feasible."
        ),
    },

    "Primary-Secondary Boiler and DHW Piping": {
        "name": "Primary–Secondary Boiler and DHW Piping Reconfiguration",
        "existing": (
            "The existing piping arrangement fully separates the space-heating and domestic hot water "
            "(DHW) systems. Space heating uses a primary loop with a secondary circulating loop, while "
            "the DHW system is served by an independent loop with no hydraulic or control integration. "
            "This layout limits temperature control during shoulder seasons and can lead to boiler "
            "short cycling, overheating, and reduced efficiency."
        ),
        "retrofit": (
            "It is recommended to reconfigure the heating and DHW piping into a Primary–Secondary (P-S) "
            "hydronic arrangement. In a P-S design, the boiler primary loop circulates hot water and "
            "secondary loops draw only the flow and temperature needed for each load, including space "
            "heating zones and DHW. This provides hydraulic separation, allows individualized water "
            "temperatures, improves outdoor-air reset control, and protects boilers from low-flow or "
            "low-return conditions. With this redesign, DHW storage capacity can be reduced and an "
            "instantaneous DHW system may be introduced. When combined with a condensing boiler retrofit, "
            "the number of boilers can often be reduced, lowering capital and long-term maintenance "
            "costs. Further engineering review is required to finalize the detailed design."
        ),
    },

    "MUA Hydronic Conversion": {
        "name": "MUA Hydronic Conversion",
        "existing": (
            "The building is served by gas-fired rooftop make-up air (MUA) units that supply tempered "
            "fresh air to the corridors. Each unit is equipped with a supply fan VFD but there is "
            "limited evidence of automated scheduling or airflow reset, and the units likely operate at "
            "constant or manually set speeds. The MUAs provide heating through integral gas burners and "
            "do not offer mechanical cooling. Components appear to be aging and operational flexibility "
            "is limited."
        ),
        "retrofit": (
            "It is recommended to convert the existing gas-fired MUAs to hydronic heating by replacing "
            "the gas sections with new hydronic coils served by the central boiler plant. Existing fans "
            "and VFDs would be retained, with new modulating valves controlling hot-water flow to "
            "maintain discharge-air temperature. Transferring the heating load to a high-efficiency "
            "condensing boiler plant will reduce natural gas use and improve performance. BAS "
            "integration will provide scheduling, temperature reset, and fan-speed control. This "
            "hydronic conversion improves efficiency, reduces operating cost, extends equipment life, "
            "and enhances corridor comfort. Enbridge incentives for central heating efficiency "
            "upgrades can help reduce project payback."
        ),
    },

    "Fan Coil to WSHP": {
        "name": "Transition Fan Coils to Water-Source Heat Pump System (Long-Term Strategy)",
        "existing": (
            "The building operates a two-pipe fan-coil system with seasonal changeover between boiler heating and "
            "chiller cooling. The system cannot provide simultaneous heating and cooling, which limits comfort during "
            "shoulder seasons and requires maintaining both the boiler and chiller plants. The existing chiller and fan "
            "coils will require major renewal in the coming years, and replacement of the central chiller alone may"
            " exceed $1 million.\n\n"
            "Given the scale of the upcoming capital work, the corporation should evaluate long-term "
            "alternatives before reinvesting in like-for-like chiller replacement"
        ),
        "retrofit": (
            "Mann recommends considering a conversion to a water-source heat pump (WSHP) system "
            "when the fan coils and chiller reach end-of-life. WSHP units can be installed within the "
            "existing fan-coil cabinets, and most of the existing piping can be retained. The chiller "
            "would be replaced with a fluid cooler, while the boiler plant would provide supplemental heat as required.\n\n"
            "A WSHP system operates on a moderate-temperature hydronic loop and allows simultaneous heating "
            "and cooling throughout the building. This eliminates seasonal changeover, reduces mechanical complexity, a"
            "nd improves energy performance. Heat can be recovered internally between zones during shoulder seasons, "
            "and boiler runtime can be significantly reduced. Over time, boiler capacity may also be downsized depending "
            "on load requirements.This measure represents a major capital transition and is not intended for "
            "immediate implementation. It should be incorporated into the building’s long-term capital plan so "
            "that WSHP conversion can be evaluated when major equipment renewal is required.\n\n"
            "* Further engineering details are required to finalize this measure."
        ),
    },

    "EV Charging Stations": {
        "name": "EV Charging Stations",
        "existing": (
            "Electric vehicle (EV) ownership is expected to grow substantially over the next decade, "
            "and many multi-residential and commercial buildings currently lack dedicated EV charging "
            "infrastructure for residents, staff, or visitors."
        ),
        "retrofit": (
            "It is recommended that the building plan and implement EV charging infrastructure to "
            "support the growing number of electric vehicles. Natural Resources Canada (NRCan) offers "
            "Zero Emission Vehicle Infrastructure (ZEVI) incentives that can cover a significant "
            "portion of the capital cost of workplace, multi-residential, and public EV charging "
            "stations. Mann can assist owners in applying for incentives, selecting appropriate "
            "charger types, and integrating the system with existing electrical infrastructure to "
            "provide reliable, future-ready EV charging service."
        ),
    },

    "BAS Install": {
        "name": "Install New Building Automation System (BAS)",
        "existing": (
            "The existing HVAC mechanical systems—including MUAs, exhaust fans, heating boilers, DHW "
            "plant, cooling equipment, and pumps—are controlled manually or via basic local "
            "thermostats and temperature sensors. There is minimal outdoor-air reset, limited boiler "
            "sequencing, and no centralized scheduling or monitoring. Equipment often operates during "
            "unoccupied periods, leading to excessive energy use and chronic overheating."
        ),
        "retrofit": (
            "It is recommended to install a centralized BAS to control all major HVAC systems. The BAS "
            "would provide occupancy-based scheduling, outdoor-temperature reset for boilers, zone-level "
            "temperature modulation, real-time monitoring, remote access, and alarm notifications. "
            "Improved control will reduce unnecessary run time, lower energy consumption, and improve "
            "comfort while reducing maintenance costs through better diagnostics. Utility incentives for "
            "advanced building controls can further improve project economics, with typical paybacks on "
            "the order of 3–4 years."
        ),
    },

    "Common Area Lighting Retrofit": {
        "name": "Common Area and Garage Lighting Retrofit",
        "existing": (
            "Common areas and the garage are illuminated primarily by 4-ft T8 fluorescent fixtures and "
            "CFL spirals controlled by manual switches. These technologies have relatively high energy "
            "use and shorter lamp life compared to modern LED lighting."
        ),
        "retrofit": (
            "Mann recommends retrofitting all existing T8 fluorescent fixtures and CFL spiral lamps with "
            "high-efficiency LED fixtures or lamps. LEDs consume significantly less electricity, have a "
            "longer lifespan, and reduce maintenance. Occupancy sensors or motion detectors should be "
            "installed in garages, mechanical rooms, laundry rooms, and other intermittently used "
            "spaces so lights operate only when needed. Daylight sensors can be added where natural "
            "light is available. This combined approach can substantially reduce electricity "
            "consumption, improve lighting quality and safety, and lower maintenance costs."
        ),
    },

    "Outdoor Reset for Hydronic Heating": {
        "name": "Outdoor Reset Control for Hydronic Heating System",
        "existing": (
            "The hydronic heating system currently operates at a fixed supply temperature of "
            "approximately 150°F regardless of outdoor conditions. Although the boilers are modern "
            "condensing units, they are controlled only by local onboard controls with no coordinated "
            "outdoor-air reset. Suite pumps operate continuously at constant speed, resulting in low "
            "temperature differential, unnecessary gas consumption, and overheating during shoulder "
            "seasons."
        ),
        "retrofit": (
            "It is recommended to implement an outdoor-air reset strategy through the BAS to reduce "
            "supply-water temperature during mild weather while maintaining design temperatures during "
            "cold conditions. The reset curve would coordinate all boilers under unified control and "
            "improve hydronic ΔT. Lower system temperatures increase the likelihood of condensing "
            "operation, reduce natural gas use, and mitigate suite overheating. As this measure is "
            "primarily software-based and leverages existing BAS infrastructure, it offers a cost-"
            "effective way to improve efficiency and comfort."
        ),
    },

    "MUA VFD Retrofit": {
        "name": "MUA VFD Retrofit",
        "existing": (
            "Corridor and common-area ventilation is provided by rooftop MUA units with constant-speed "
            "supply fans. These fans run at full speed whenever the units are enabled, independent of "
            "actual ventilation demand or occupancy. This results in higher electrical consumption and "
            "increased wear on motors and drive components."
        ),
        "retrofit": (
            "It is recommended to retrofit the MUA supply fans with variable frequency drives (VFDs) "
            "and integrate them with the BAS. Fan speed would be reset based on duct static pressure, "
            "temperature, schedule, or occupancy. Under typical conditions, fan speed would be reduced "
            "during low-load periods while maintaining the ability to ramp up when higher ventilation "
            "rates are required. This measure reduces fan energy use, lowers mechanical stress, extends "
            "equipment life, and improves control of building pressurization and corridor comfort."
        ),
    },

    "BAS Recommission – Valves": {
        "name": "BAS Recommissioning – Control Valves",
        "existing": (
            "BAS graphics and trend data indicate that some control valves do not respond correctly to "
            "commands, with mismatched command and feedback values. This suggests failed actuators, "
            "sensor issues, or incorrect control logic, which can lead to poor temperature control and "
            "inefficient operation."
        ),
        "retrofit": (
            "A BAS recommissioning effort is recommended focusing on valve operation. The work would "
            "include verification of valve stroke and response, recalibration or replacement of faulty "
            "sensors, correction of point mapping, and adjustment of control logic. Restoring proper "
            "valve control will improve temperature stability, ensure accurate BAS monitoring, and "
            "reduce energy waste associated with malfunctioning or overridden valves."
        ),
    },

    "DHW Repiping for Condensing Boilers": {
        "name": "DHW Repiping for Condensing Boiler Performance",
        "existing": (
            "The domestic hot water (DHW) system is piped such that cold domestic water first enters "
            "the storage tank and then returns pre-warmed to the condensing boilers. This elevated "
            "boiler entering-water temperature results in a very low ΔT across the boilers and prevents "
            "them from operating in true condensing mode, reducing seasonal efficiency and increasing "
            "gas consumption."
        ),
        "retrofit": (
            "It is recommended to repipe the DHW system so that cold domestic water is brought directly "
            "to the boiler inlet, with the storage tank used primarily for volume and buffering. This "
            "configuration lowers boiler entering-water temperature, increases ΔT, and allows the "
            "condensing boilers to operate within their intended condensing range. The retrofit will "
            "improve efficiency, reduce gas usage, and better align DHW system performance with modern "
            "condensing boiler capabilities."
        ),
    },

    "MUA Hydronic + BAS + VFD": {
        "name": "MUA Hydronic Conversion with BAS and VFDs",
        "existing": (
            "The building is served by gas-fired DX rooftop MUA units that provide tempered fresh air "
            "to corridors. Units have limited modulation capability, appear to operate at constant or "
            "manually set speeds, and are not fully integrated with the BAS. Burners, DX sections, and "
            "controls are aging, and continuous or high airflow during mild weather contributes to "
            "excessive gas and electrical consumption."
        ),
        "retrofit": (
            "It is recommended to convert the DX gas-fired MUAs to hydronic heating served by the "
            "central boiler plant, add VFDs on supply fans where feasible, and fully integrate the "
            "units with the BAS. New hydronic coils, modulating dampers, fan-speed control, and "
            "supply-air temperature reset will allow demand-based ventilation and improved corridor "
            "pressurization. Transferring heating to a high-efficiency condensing boiler plant will "
            "reduce gas use, while VFDs lower fan energy and mechanical wear. BAS integration will "
            "enable optimized scheduling, monitoring, and alarms. Enbridge incentives for central "
            "heating and control upgrades can help improve project payback."
        ),
    },
})
MEASURE_TEMPLATES.update({
    "Enbridge Gas Boiler Optimization Pilot Program": {
        "name": "Boiler Plant Optimization & Hydronic Balancing",
        "existing": (
            "The central heating plant consists of eight (8) condensing boilers installed circa 2014. Although the boilers "
            "are designed for high-efficiency condensing operation, the system is currently operated with elevated supply-water"
            " temperatures, with observed setpoints typically in the range of approximately 140°F to 150°F. Based on operator "
            "feedback, these aggressive setpoints are maintained to satisfy the heating demands of the Make-Up Air (MUA) units,"
            " which share the primary heating loop, and to compensate for localized flow restrictions within the distribution piping.\n\n"
            "Under these operating conditions, return-water temperatures are likely elevated for much of the heating season, limiting "
            "the boilers’ ability to operate in condensing mode and effectively reducing efficiency to non-condensing levels. "
            "The existing hydronic configuration does not provide sufficient separation between the higher-temperature MUA"
            "loads and the lower-temperature building heating loop, restricting the ability to reset supply temperatures independently."
        ),
        "retrofit": (
            "Mann recommends pursuing boiler plant optimization through the Enbridge Gas Boiler Optimization "
            "Pilot Program. This program supports optimization of existing boiler plants through a phased approach "
            "rather than equipment replacement. The initial phase includes a detailed engineering assessment, funded "
            "by the program, to evaluate system flow characteristics, control limitations, and hydronic configuration.\n\n"
            "Based on the assessment findings, the retrofit scope may include hydronic separation between the MUA and "
            "building heating loops, corrective system balancing to address flow restrictions, and optimization of BAS"
            " control strategies. These measures would allow the boiler outdoor-air reset curve to be lowered while "
            "maintaining adequate MUA heating, enabling return-water temperatures to drop into the condensing range.\n\n"
            "This approach restores the boiler plant closer to its intended design performance, increases seasonal "
            "efficiency, and maximizes the value of the existing assets without the capital cost of boiler replacement."
        ),
    },

    "Gas Co-Generation (CHP)": {
        "name": "Natural Gas Co-Generation (CHP) System",
        "existing": (
            "The building is heated by a central boiler plant that serves space heating, domestic hot "
            "water and, where applicable, pool loads. All electricity is purchased from the grid and there "
            "is no on-site generation. Existing equipment such as make-up air units may be older or "
            "decommissioned, and there is no reuse of waste heat from power generation."
        ),
        "retrofit": (
            "It is recommended to consider installing a natural-gas-fired combined heat and power (CHP) "
            "system. The CHP unit would generate electricity on site to offset grid demand while recovering "
            "waste heat through hydronic loops to preheat the central heating and/or domestic hot water "
            "systems. Excess heat could be rejected to a fluid cooler when not needed. A properly sized "
            "CHP plant can improve overall site efficiency, reduce utility costs and provide partial backup "
            "capability during power outages. Incentive programs may be available to support feasibility "
            "studies and capital costs. Detailed engineering is required to confirm sizing, interconnection "
            "requirements and economic performance."
        ),
    },

    "Fan Coil Unit Retrofit": {
        "name": "Fan Coil Unit Retrofit – Suite Units",
        "existing": (
            "Each suite is currently served by a fan-coil unit (FCU) that provides heating and cooling from "
            "central hydronic risers. Many FCUs are original to the building and have reached or exceeded "
            "their expected service life. The original manufacturer may no longer support the product, "
            "making parts replacement and servicing increasingly difficult and leading to comfort and "
            "maintenance issues."
        ),
        "retrofit": (
            "It is recommended to plan a staged retrofit of the suite fan-coil units. One option is to "
            "replace perimeter radiators with new heat/cool FCUs tied into the building automation system "
            "to provide limited but controlled tenant setpoint adjustment while using existing perimeter "
            "risers. An alternative is to replace the existing central FCUs with new units in the same "
            "locations using existing risers, retaining existing perimeter radiators. The preferred option "
            "will depend on the condition of the risers, architectural constraints and tenant impacts. A "
            "detailed engineering study is required to evaluate riser condition, hydraulic capacity and "
            "construction phasing."
        ),
    },

    "Garage CO Sensors": {
        "name": "Garage Exhaust CO Sensor Control",
        "existing": (
            "Garage exhaust fans are currently controlled by time schedules or manual switches, with no "
            "carbon monoxide (CO) detection system. Fans may operate even when pollutant levels are low, "
            "and at times CO concentrations can exceed recommended thresholds before fans are activated."
        ),
        "retrofit": (
            "It is recommended to install a CO-based control system for the garage exhaust fans. CO sensors "
            "would be strategically located throughout the garage and connected to fan starters or the BAS. "
            "Fans would operate only when CO concentrations exceed programmable setpoints and would shut "
            "off or reduce speed when levels are low. This approach maintains air quality while reducing "
            "fan run hours, electrical energy use and noise. Further engineering is required to determine "
            "sensor locations, control sequences and integration details."
        ),
    },

    "DHW Condensing Boiler Replacement": {
        "name": "Replace DHW Boiler with Condensing Boiler",
        "existing": (
            "The domestic hot water (DHW) system is currently served by an atmospheric gas-fired boiler that "
            "is near or past the end of its typical service life. Atmospheric boilers have relatively low "
            "thermal efficiency, high standby losses and limited turndown capability. As equipment ages, "
            "efficiency and reliability decline and the risk of failure increases."
        ),
        "retrofit": (
            "It is recommended to replace the existing atmospheric DHW boiler with a new high-efficiency "
            "condensing boiler, typically rated around 95% thermal efficiency. The new boiler would be "
            "equipped with fully modulating burners and integrated controls to match output to DHW demand, "
            "reducing cycling and standby losses. Piping can be reconfigured to minimize standby heat loss "
            "and protect the boiler from thermal shock. This retrofit will improve energy efficiency, "
            "enhance reliability and reduce safety concerns associated with aging atmospheric equipment. "
            "Additional engineering is required to confirm sizing, venting and integration with the "
            "existing DHW system."
        ),
    },

    "Cooling Tower Fan VFD": {
        "name": "Cooling Tower Fan VFD Retrofit",
        "existing": (
            "The cooling tower is equipped with constant-speed or multi-speed fan motors that operate at "
            "discrete speeds regardless of the actual cooling load. Under part-load conditions, the fans "
            "still consume close to full power, resulting in unnecessary electrical usage and increased "
            "wear on mechanical components."
        ),
        "retrofit": (
            "It is recommended to install variable frequency drives (VFDs) on the cooling tower fan motors. "
            "VFDs will allow fan speed to be modulated based on condenser water temperature, ambient "
            "conditions or BAS commands, so airflow more closely matches the required cooling load. "
            "Reducing fan speed yields large electrical savings due to the cubic relationship between power "
            "and speed, while also reducing noise and extending equipment life. Controls and safeties must "
            "be updated and commissioned as part of this measure."
        ),
    },

    "Booster Pump VFD": {
        "name": "Booster Pump VFD Retrofit",
        "existing": (
            "Domestic cold water is currently pressurized by a constant-speed booster pump with a downstream "
            "pressure-reducing or regulating valve to maintain setpoint pressure. The valve introduces "
            "unnecessary head loss and wastes pumping energy, and the pump operates at full speed even when "
            "demand is low."
        ),
        "retrofit": (
            "It is recommended to install a variable frequency drive (VFD) on the domestic water booster "
            "pump and remove or bypass the pressure regulating valve. The VFD will control pump speed to "
            "maintain the desired discharge pressure directly, allowing the pump to slow down during "
            "periods of low demand. This reduces energy use, pump wear and noise while maintaining adequate "
            "system pressure. Further engineering is required to confirm setpoints, sensor locations and "
            "control logic."
        ),
    },

    "Misc Maintenance Upgrades": {
        "name": "Miscellaneous Maintenance and Efficiency Upgrades",
        "existing": (
            "Several mechanical and electrical systems in the building rely on routine maintenance to "
            "maintain efficiency, but many components have not been proactively upgraded or recommissioned. "
            "Heat exchangers may have scale or fouling, older motors may be standard-efficiency models, and "
            "controls or thermostats may be outdated or non-programmable."
        ),
        "retrofit": (
            "It is recommended to implement a package of miscellaneous maintenance and upgrade items. "
            "Typical measures include cleaning and descaling heat exchangers, replacing failed or obsolete "
            "motors with high-efficiency models, maintaining combustion air paths, upgrading in-suite "
            "appliances to ENERGY STAR models as they fail, and replacing non-programmable thermostats with "
            "programmable or smart thermostats. These actions reduce long-term maintenance costs, improve "
            "system efficiency and extend equipment life with relatively low capital investment."
        ),
    },

    "Packaged Heating/Cooling MUA": {
        "name": "Replace Existing MUA with Packaged Heating/Cooling MUA",
        "existing": (
            "Existing make-up air (MUA) units operate at constant volume with limited runtime scheduling and "
            "no demand-based control. Many units provide little or no heating or cooling capability and are "
            "not equipped with CO₂ sensors or variable-speed fans, resulting in over-ventilation and higher "
            "energy use."
        ),
        "retrofit": (
            "It is recommended to replace the existing MUA units with new packaged heating and cooling units "
            "equipped with variable-speed fans and CO₂-based demand control ventilation. The new MUAs would "
            "adjust outdoor-air volume to maintain indoor air quality while minimizing unnecessary "
            "ventilation during low-occupancy periods. Integration with the BAS will allow scheduling, "
            "temperature reset and alarm monitoring. This measure improves comfort, air quality and energy "
            "performance while renewing end-of-life ventilation equipment."
        ),
    },

    "Upper MUA Hydronic Conversion": {
        "name": "Convert Upper MUA to Hydronic Heating",
        "existing": (
            "The upper make-up air unit uses an integral atmospheric gas burner to heat 100% outdoor air, "
            "often running continuously. This design has relatively low efficiency, high standby losses and "
            "limited modulation capability, particularly during part-load conditions."
        ),
        "retrofit": (
            "It is recommended to convert the upper MUA to hydronic heating supplied by a high-efficiency "
            "condensing boiler. The gas burner would be replaced with a hot-water coil connected to the "
            "central boiler plant, with modulating valves controlled by the BAS. Hydronic conversion "
            "reduces direct gas consumption at the MUA, improves control, and allows the central plant to "
            "operate at higher efficiency. Piping and controls will need to be modified to protect the "
            "boiler and minimize standby losses."
        ),
    },

    "Solar Preheat – Upper MUA": {
        "name": "Solar Air Pre-Heating for Upper MUA",
        "existing": (
            "The upper MUA currently introduces and heats 100% cold outdoor air during the winter season. "
            "All heating energy for this large airflow is provided by the existing heating system, "
            "resulting in substantial gas consumption."
        ),
        "retrofit": (
            "It is recommended to install a solar air heating system to preheat the outdoor air supplied to "
            "the upper MUA. Solar collector panels would be installed on suitable south-facing façades and "
            "ducted to the MUA, raising incoming air temperature using free solar energy before it enters "
            "the heating coil. This reduces gas consumption at the unit and lowers operating costs. Further "
            "engineering is required to confirm available façade area, integration details and structural "
            "constraints."
        ),
    },

    "Solar Preheat – DHW": {
        "name": "Solar Pre-Heating for Domestic Hot Water",
        "existing": (
            "Domestic hot water is currently produced entirely by gas-fired equipment, with no renewable "
            "pre-heating. All hot water load is met by the boiler plant, resulting in higher gas "
            "consumption and associated emissions."
        ),
        "retrofit": (
            "It is recommended to consider a solar thermal system to preheat domestic hot water. Roof-"
            "mounted solar collectors would transfer heat via a glycol loop and heat exchanger to a "
            "storage tank, with the existing DHW boiler serving as backup. Solar pre-heating can reduce "
            "gas consumption and provide long-term energy savings, especially in buildings with high year-"
            "round DHW loads. Incentive programs may be available, although payback periods are often "
            "longer than for other measures. Detailed engineering is required to evaluate roof space, "
            "structural capacity and economic feasibility."
        ),
    },
    "DHW retrofit + plate and frame HX + mixing valve": {
        "name": "DHW retrofit with plate and frame Heat exchanger",
        "existing": (
            "The domestic hot water (DHW) system is served by an indirect storage tank connected to the central boiler "
            "plant. The storage tank, associated DHW circulation pumps, and portions of the DHW piping were observed to "
            "be original to the building and approaching the end of their expected service life. In addition, no anti-scald "
            "mixing valve was observed at the DHW storage tank, limiting temperature control and presenting a potential safety concern."
            "Aging indirect tanks typically require periodic internal relining and ongoing maintenance to maintain performance and water "
            "quality. As these components continue to age, maintenance requirements and the risk of unplanned service interruptions are expected to increase "
        ),
        "retrofit": (
            "As part of the boiler plant and hydronic system reconfiguration, Mann recommends upgrading the DHW system "
            "by replacing the existing indirect storage tank with vertical glass-lined storage tanks served by a "
            "plate-and-frame heat exchanger. This configuration provides improved heat-transfer performance, more stable "
            "DHW temperature control, and greater flexibility for maintenance and future system modifications."
            "Glass-lined storage tanks offer longer service life and reduced internal maintenance requirements "
            "compared to older steel-lined indirect tanks. The plate-and-frame heat exchanger allows efficient heat "
            "transfer while simplifying inspection, cleaning, and servicing activities relative to integrated indirect "
            "tank designs. Incorporating a thermostatic mixing valve as part of this retrofit will further improve temperature control and occupant safety."
            "This DHW retrofit reduces long-term maintenance requirements, improves system reliability, and aligns "
            "with the overall mechanical room modernization strategy by supporting a more modular and serviceable system layout"
        ),
    },

    "Dry-O-Tron Pool Unit": {
        "name": "Replace Pool AHU and Exhaust Fan with Dry-O-Tron Unit",
        "existing": (
            "The swimming pool area is currently served by a conventional air-handling unit and separate "
            "exhaust fan. Humidity control is limited, and there is no integrated heat recovery between "
            "exhaust and supply air. This can lead to higher space heating loads, condensation issues and "
            "comfort complaints in the pool area."
        ),
        "retrofit": (
            "It is recommended to replace the existing pool AHU and exhaust fan with a packaged "
            "dehumidification unit such as a Dry-O-Tron. This type of system combines dehumidification, "
            "space heating and exhaust heat recovery in a single unit, controlling humidity and pool water "
            "temperature to defined setpoints. Recovered heat can be used to warm supply air or pool water, "
            "reducing overall energy consumption. Detailed engineering is required to size the unit and "
            "confirm ductwork and structural requirements."
        ),
    },

    "Roof MUA Heat Recovery": {
        "name": "Heat Recovery for Roof MUA and Exhaust Fans",
        "existing": (
            "Roof-level make-up air units and associated exhaust fans currently operate as separate systems, "
            "with exhaust air discharged directly outdoors. This configuration wastes the sensible and "
            "latent energy contained in the exhaust stream, increasing heating and cooling loads on the "
            "supply air systems."
        ),
        "retrofit": (
            "It is recommended to install heat recovery coils or a similar energy-recovery device between "
            "the exhaust and outdoor air streams serving roof-level MUAs. Energy-recovery coils or other "
            "heat exchangers would be installed in the supply and exhaust ducts to transfer heat (and "
            "potentially moisture) from exhaust air to incoming outdoor air. This reduces the heating and "
            "cooling energy required to condition ventilation air. A detailed engineering study is required "
            "to confirm duct capacities, fan static pressure allowances and space constraints."
        ),
    },

    "Adding a Heat Exchanger to Isolate the Glycol Tower Loop from the Building Loop": {
        "name": "Adding a Heat Exchanger to Isolate the Glycol Tower Loop from the Building Loop",
        "existing": (
            "The WSHP loop operates with a 25% glycol mixture for freeze protection. A glycol feed system is present; "
            "however, the feed tank level was observed to be low at the time of the site visit. "
            "The current hydronic configuration also appears to allow glycol to circulate through both the cooling tower "
            "loop and the building loop. This arrangement significantly increases the total system glycol volume, "
            "resulting in higher chemical cost, more frequent testing, and increased maintenance requirements. "
            "Without dedicated hydraulic separation between the tower loop and the building loop, glycol is introduced "
            "into portions of the system where freeze protection is not required, complicating long-term operation and "
            "increasing the risk of concentration imbalance between loops.\n\n"
            "No major operational issues were reported at the time of the walkthrough, targeted improvements would improve "
            "freeze protection reliability, reduce chemical costs, and enhance overall WSHP loop stability."
        ),
        "retrofit": (
            "Install a plate-and-frame heat exchanger to hydraulically isolate the glycol cooling-tower loop from the "
            "building loop and stabilize glycol concentration control.Only the tower loop will require glycol going forward, "
            "significantly reducing the total glycol volume needed, lowering chemical costs, and improving long-term system "
            "efficiency. Hydraulic isolation also reduces the risk of glycol contamination, improves maintenance simplicity, "
            "and enhances overall operational reliability."
            "This upgrades provide a robust freeze-protection strategy, reduce chemical and maintenance costs, and improve "
            "WSHP loop stability and building mechanical system performance. Replacement can be considered in the short term"
        ),
    },

    "Gas Dryer Replacement": {
        "name": "Replace Electric Dryers with Natural Gas Dryers",
        "existing": (
            "Common-area laundry facilities currently use electric dryers, which consume a significant amount "
            "of electricity for each drying cycle. Electrical operating costs are relatively high compared "
            "to equivalent natural-gas-fired equipment."
        ),
        "retrofit": (
            "It is recommended to replace existing electric dryers in the laundry room with high-efficiency "
            "natural-gas-fired dryers, where gas service and venting are feasible. Gas dryers typically have "
            "lower energy costs per cycle and can provide shorter drying times. This measure reduces "
            "electricity demand and can be implemented during normal equipment replacement cycles."
        ),
    },

    "Gas Unit Heaters – Space Heating": {
        "name": "Install Natural Gas Unit Heaters for Space Heating",
        "existing": (
            "Space heating in certain areas of the building is currently provided by electric baseboard heaters "
            "or other electric resistance equipment. Electric resistance heating has high operating costs and "
            "places a large demand on the electrical system."
        ),
        "retrofit": (
            "Where suitable, it is recommended to install vented natural-gas-fired unit heaters to replace or "
            "supplement electric resistance heating. Gas unit heaters can provide the same heating output at "
            "lower operating cost, reducing electrical demand and utility bills. A feasibility review is "
            "required to confirm gas availability, flue routing and ventilation requirements."
        ),
    },

    "New Chiller Replacement": {
        "name": "Replace Existing Chiller with High-Efficiency Chiller",
        "existing": (
            "The existing chiller is an older unit approaching or exceeding its typical service life and uses "
            "an outdated refrigerant. Older chillers generally operate at lower efficiency than modern "
            "equipment and may have higher maintenance requirements and reliability concerns."
        ),
        "retrofit": (
            "It is recommended to replace the existing chiller with a new high-efficiency chiller, such as a "
            "scroll or centrifugal unit with modern controls and BAS integration. The new chiller can offer "
            "improved part-load performance, variable-speed compression, environmentally preferable "
            "refrigerants and enhanced protection features. This upgrade will improve cooling efficiency, "
            "reduce maintenance and improve occupant comfort during hot weather."
        ),
    },

    "Common Area Occupancy Sensors": {
        "name": "Common Area Lighting Occupancy Sensors",
        "existing": (
            "Common areas such as corridors, stairwells, mechanical rooms and laundry rooms are illuminated by "
            "fluorescent or LED fixtures controlled mainly by manual switches. Lights often remain on when "
            "spaces are unoccupied, resulting in unnecessary electricity consumption."
        ),
        "retrofit": (
            "It is recommended to install motion or occupancy sensors to control lighting in low-occupancy "
            "areas. Sensors would switch lights on when motion is detected and off after a programmed time "
            "delay. This measure can be implemented alongside LED retrofits to further reduce lighting energy "
            "use and maintenance requirements while maintaining adequate illumination when spaces are in use."
        ),
    },

    "Window Retrofit": {
        "name": "Window Retrofit – High-Performance Glazing",
        "existing": (
            "The building exterior is glazed with a mix of older single- and double-glazed aluminum-frame "
            "windows with relatively high U-values and limited thermal breaks. Large glazing areas increase "
            "heat loss in winter and heat gain in summer, contributing to higher heating and cooling loads. "
            "Condensation around frames has caused localized damage in some areas."
        ),
        "retrofit": (
            "It is recommended to retrofit the windows with new high-performance units, such as double- or "
            "triple-glazed, low-emissivity, argon-filled glazing with thermally broken frames. Upgraded "
            "windows will reduce heat loss in winter and solar gain in summer, improving energy performance "
            "and occupant comfort by increasing interior surface temperatures and reducing drafts. The "
            "potential for condensation and related damage will also be reduced. Detailed energy modelling "
            "is recommended to quantify savings and support capital planning."
        ),
    },

    "Window Caulking Upgrade": {
        "name": "Window Caulking / Weatherstripping Upgrade",
        "existing": (
            "Existing windows show signs of aging sealants and caulking around frames, contributing to air "
            "leakage and localized condensation. While full window replacement would address both conduction "
            "and air leakage, it represents a major capital expense."
        ),
        "retrofit": (
            "As a lower-cost alternative or interim measure, it is recommended to renew exterior window "
            "caulking and weatherstripping. Re-caulking helps reduce uncontrolled air infiltration, improving "
            "thermal comfort and lowering heating energy use, although it does not significantly change the "
            "thermal performance of the glazing itself. This measure can be implemented as part of routine "
            "envelope maintenance or in preparation for future full window replacement."
        ),
    },

    "Power Factor Correction": {
        "name": "Install Power Factor Correction Equipment",
        "existing": (
            "Large inductive loads such as pumps, fans and chillers reduce the building’s electrical power "
            "factor below utility targets, leading to higher apparent power demand and potential penalties or "
            "inefficiencies on the electrical system."
        ),
        "retrofit": (
            "It is recommended to install power factor correction capacitors or integrated correction "
            "equipment on major motor loads that are not served by variable frequency drives. Improving power "
            "factor closer to unity reduces reactive power, lowers kVA demand and can reduce electricity "
            "charges. Detailed electrical analysis is required to size and locate correction devices and to "
            "ensure compatibility with existing equipment."
        ),
    },

    "Heating System Recommissioning": {
        "name": "Heating System Recommissioning",
        "existing": (
            "The existing boiler plant and associated hydronic systems have been in service for many years. "
            "Although some boilers are high-efficiency models, performance can degrade over time due to "
            "combustion drift, fouled heat-transfer surfaces, damaged insulation and suboptimal control "
            "settings. Standby losses and boiler cycling may be higher than necessary."
        ),
        "retrofit": (
            "It is recommended to undertake a recommissioning program for the heating system. Typical scope "
            "includes combustion analysis and tuning of all boilers, repair or replacement of damaged "
            "insulation, verification of pump and valve operation, adjustment of schedules and temperature "
            "setpoints, and correction of identified leaks or control issues. Recommissioning restores "
            "systems closer to design performance, reduces energy waste and can often be supported by utility "
            "incentive programs."
        ),
    },

    "Separate Garage Exhaust from Cooling Tower": {
        "name": "Separate Garage Exhaust from Cooling Tower Well",
        "existing": (
            "Garage exhaust air is currently discharged into the same shaft or well that houses the cooling "
            "tower. During cooling operation, the tower draws a mixture of outdoor air and warm, contaminated "
            "garage exhaust, which can degrade cooling tower performance, reduce capacity on hot days and "
            "increase corrosion and fouling risks."
        ),
        "retrofit": (
            "It is recommended to separate the garage exhaust air from the cooling tower well by rerouting "
            "exhaust to a dedicated shaft or exterior discharge point and providing adequate outdoor-air "
            "openings for the cooling tower. Additional louvers may be required to ensure proper airflow. If "
            "separation is not feasible, the cooling tower may need to be upsized. This measure primarily "
            "improves cooling reliability and capacity, with secondary energy benefits from more efficient "
            "tower operation. Structural and mechanical engineering review is required."
        ),
    },

    "Geothermal Upgrade": {
        "name": "Geothermal Upgrade for Heat Pump Loop",
        "existing": (
            "The building uses a central heat pump loop with boilers providing heat in winter and a cooling "
            "tower rejecting heat in summer. Boilers and the cooling tower operate year-round to maintain "
            "loop temperature, resulting in significant gas and electricity consumption."
        ),
        "retrofit": (
            "It is recommended to evaluate the feasibility of adding a geothermal or ground-source heat "
            "exchange loop to supplement the existing heat pump loop. A vertical or horizontal ground loop "
            "would exchange heat with the earth, reducing reliance on boilers and the cooling tower. "
            "Geothermal heat pumps can provide efficient heating and cooling by leveraging relatively stable "
            "ground temperatures. This upgrade can reduce operating costs and emissions but requires "
            "detailed geotechnical, structural and mechanical analysis to confirm compatibility with the "
            "existing heat pump system and available site area."
        ),
    },
})
# --- Short summaries for measure summary table --- #
MEASURE_SUMMARIES = {
    "BAS Upgrade": (
        "Upgrade legacy local controls to a modern integrated BAS, enabling central scheduling, "
        "reset strategies and fault monitoring to reduce energy use and improve comfort."
    ),
    "Condensing Boiler Retrofit": (
        "Replace aging near-condensing boilers with high-efficiency condensing units and improved piping "
        "to enable true condensing operation, lowering gas consumption and extending plant life."
    ),
    "Fancoil to WSHP(short term)": (
        "Replace seasonal fan-coil system with water-source heat pumps on a moderate-temperature loop"
        "allowing simultaneous heating and cooling and eliminating the central chiller."
    ),
    "Investigate Electric Heating": (
        "Identify and eliminate or optimise all resistive electric heating loads operating in winter to "
        "reduce unusual seasonal electricity spikes and lower overall energy costs."
    ),

    "Existing BAS Upgrade": (
        "Modernise the existing BAS and field devices onto an open digital platform with full feedback, "
        "trending and alarms to improve reliability, visibility and HVAC optimisation opportunities."
    ),
    "Sub-metering": (
        "Install certified electrical sub-meters on main feeds to enable consumption-based billing and "
        "end-use tracking, typically driving 5–30% electricity savings per suite."
    ),
    "Primary-Secondary Boiler and DHW Piping": (
        "Reconfigure heating and DHW piping to a primary–secondary layout, hydraulically separating loops "
        "to improve temperature control, boiler protection and plant efficiency."
    ),
    "MUA Hydronic Conversion": (
        "Convert gas-fired MUAs to hydronic coils served by a central condensing boiler plant, with BAS "
        "control and VFDs to improve ventilation efficiency and reduce gas use."
    ),
    "Fan Coil to WSHP": (
        "Replace seasonal fan-coil system with water-source heat pumps on a moderate-temperature loop, "
        "allowing simultaneous heating and cooling and eliminating the central chiller."
    ),
    "EV Charging Stations": (
        "Plan and install EV charging infrastructure for residents and staff, leveraging NRCan ZEVI "
        "incentives to offset capital cost and future-proof the facility."
    ),
    "BAS Install": (
        "Install a new central BAS to coordinate boilers, DHW, MUAs, pumps and exhaust fans with "
        "scheduling, reset and remote access, reducing energy use and maintenance."
    ),
    "Common Area Lighting Retrofit": (
        "Retrofit T8 and CFL lighting in common areas and garages to LED with occupancy/daylight controls "
        "to cut electricity use and maintenance while improving lighting quality."
    ),
    "Outdoor Reset for Hydronic Heating": (
        "Implement outdoor-air reset on the hydronic heating system so supply temperatures drop in mild "
        "weather, increasing condensing hours and reducing overheating and gas use."
    ),
    "MUA VFD Retrofit": (
        "Add VFDs to MUA supply fans with BAS integration so airflow tracks actual ventilation demand, "
        "cutting fan energy and mechanical wear while maintaining corridor pressure."
    ),
    "BAS Recommission – Valves": (
        "Recommission BAS control valves by verifying stroke, feedback and logic to restore proper "
        "temperature control and eliminate energy waste from failed or overridden actuators."
    ),
    "DHW Repiping for Condensing Boilers": (
        "Repipe the DHW system so cold water enters boilers directly, lowering return temperature, "
        "increasing ΔT and enabling true condensing boiler operation."
    ),
    "MUA Hydronic + BAS + VFD": (
        "Convert DX gas MUAs to hydronic coils with VFD fans and full BAS control, combining high-"
        "efficiency central heating with demand-based ventilation and fan turndown."
    ),

    "Enbridge Gas Boiler Optimization Pilot Program": (
        "Optimize the existing boiler plant through hydronic and control improvements to restore condensing performance "
        "without replacing major equipment. Qualified for Enbridge incentives."
    ),
    "Gas Co-Generation (CHP)": (
        "Install a natural-gas CHP system to generate on-site electricity and recover waste heat for "
        "heating/DHW, improving overall efficiency and resilience with potential incentives."
    ),
    "Fan Coil Unit Retrofit": (
        "Replace aging suite fan-coil units with new equipment or perimeter FCUs tied into BAS, improving "
        "comfort, serviceability and hydronic control while renewing end-of-life units."
    ),
    "Garage CO Sensors": (
        "Add CO sensors to control garage exhaust fans so they operate only when pollutant levels rise, "
        "maintaining air quality while reducing fan run hours and energy use."
    ),
    "DHW Condensing Boiler Replacement": (
        "Replace atmospheric DHW boiler with a high-efficiency condensing model and optimised piping to "
        "lower gas use, increase reliability and improve safety."
    ),
    "Cooling Tower Fan VFD": (
        "Install VFDs on cooling-tower fans so speed modulates with load, yielding large fan-energy "
        "savings and quieter, smoother operation."
    ),
    "Booster Pump VFD": (
        "Convert the constant-speed domestic booster pump to VFD control, eliminating throttling losses "
        "and matching pressure to demand for significant pump-energy savings."
    ),
    "Misc Maintenance Upgrades": (
        "Implement a bundle of low-cost maintenance upgrades—cleaning heat exchangers, replacing old "
        "motors, improving appliances and thermostats—to recover lost efficiency and reduce failures."
    ),
    "Packaged Heating/Cooling MUA": (
        "Replace existing MUAs with packaged units that provide heating, cooling, variable airflow and "
        "CO₂-based control, improving IAQ, comfort and ventilation efficiency."
    ),
    "Upper MUA Hydronic Conversion": (
        "Convert the upper MUA’s atmospheric gas burner to a hydronic coil served by a condensing boiler, "
        "reducing direct gas use and improving modulation and control."
    ),
    "Solar Preheat – Upper MUA": (
        "Install solar air-heating panels to pre-warm outdoor air for the upper MUA, offsetting winter "
        "ventilation heating gas with free solar energy."
    ),
    "Solar Preheat – DHW": (
        "Add a solar thermal pre-heat system for domestic hot water, reducing gas use for DHW production "
        "and leveraging renewable energy where roof area allows."
    ),
    "DHW retrofit + plate and frame HX + mixing valve": (
        "This measure reduces annual maintenance costs, simplify future maintenance tasks, shortens service downtime, and enhances overall system reliability and efficiency."
    ),
    
    "Dry-O-Tron Pool Unit": (
        "Replace the pool AHU and exhaust fan with a Dry-O-Tron-type dehumidification unit that recovers "
        "heat while tightly controlling pool humidity and temperature."
    ),
    "Roof MUA Heat Recovery": (
        "Add heat-recovery coils or similar devices between exhaust and outdoor-air streams on roof MUAs "
        "to reclaim energy and cut ventilation heating and cooling loads."
    ),
    "Adding a Heat Exchanger to Isolate the Glycol Tower Loop from the Building Loop": (
        "Install a plate-and-frame heat exchanger to hydraulically isolate the glycol cooling-tower loop from the building loop and stabilize glycol concentration control."
    ),
    "Gas Dryer Replacement": (
        "Replace common-area electric dryers with high-efficiency natural-gas dryers to lower electricity "
        "demand and cycle costs while maintaining drying performance."
    ),
    "Gas Unit Heaters – Space Heating": (
        "Where practical, replace electric resistance space heating with vented natural-gas unit heaters "
        "to reduce operating cost and electrical demand."
    ),
    "New Chiller Replacement": (
        "Replace the aging, low-efficiency chiller using obsolete refrigerant with a modern high-"
        "efficiency unit integrated to BAS for better cooling performance and reliability."
    ),
    "Common Area Occupancy Sensors": (
        "Install motion/occupancy sensors on common-area lighting so fixtures operate only when spaces "
        "are in use, further reducing lighting energy use."
    ),
    "Window Retrofit": (
        "Upgrade existing glazing to high-performance, thermally broken, low-E windows to reduce heat "
        "loss/gain, improve comfort and mitigate condensation issues."
    ),
    "Window Caulking Upgrade": (
        "Renew window caulking and weatherstripping to cut uncontrolled air leakage as a lower-cost "
        "envelope improvement or interim step before full window replacement."
    ),
    "Power Factor Correction": (
        "Install power-factor correction equipment on major motor loads to reduce reactive power, lower "
        "kVA demand and potentially decrease electricity charges."
    ),
    "Heating System Recommissioning": (
        "Recommission the boiler plant and hydronic system—tuning combustion, fixing insulation and "
        "optimising controls—to restore near-design efficiency and reliability."
    ),
    "Separate Garage Exhaust from Cooling Tower": (
        "Separate garage exhaust from the cooling-tower well and improve tower ventilation so the tower "
        "draws clean outdoor air, restoring capacity and efficiency on hot days."
    ),
    "Geothermal Upgrade": (
        "Add a geothermal ground loop to support the heat-pump loop, reducing boiler and cooling-tower "
        "run time and providing low-carbon heating and cooling."
    ),
}

# 把 summary 填回主模板
for key, summary in MEASURE_SUMMARIES.items():
    if key in MEASURE_TEMPLATES:
        MEASURE_TEMPLATES[key]["summary"] = summary

# ----------- Measure categories（自己可以再调名字）-----------

CATEGORIES = [
    ("BAS / Controls",       "bas"),
    ("Boiler / Plant",       "boiler"),
    ("MUA / Ventilation",    "mua"),
    ("Hydronic Loops",       "loop"),
    ("Lighting",             "lighting"),
    ("Building Envelope",    "envelope"),
    ("Water & DHW",          "water"),
    ("Pumps / Power / PF",   "pumps"),
    ("Other / Misc",         "other"),
]

# 每个 measure 对应一个类别代码（不全的你可以再慢慢补）
CATEGORY_BY_MEASURE = {
    # ---- BAS / Controls ----
    "BAS Upgrade":                          "bas",
    "Existing BAS Upgrade":                 "bas",
    "BAS Install":                          "bas",
    "BAS Recommission – Valves":           "bas",
    "Outdoor Reset for Hydronic Heating":   "bas",
    "Recommission of BAS System Install Outdoor Reset Control for Hydronic Heating System": "bas",

    # ---- Boiler / Plant ----
    "Condensing Boiler Retrofit":           "boiler",
    "DHW Condensing Boiler Replacement":    "boiler",
    "DHW Repiping for Condensing Boiler Performance": "boiler",
    "DHW Repiping for Condensing Boilers":  "boiler",

    # ---- MUA / Ventilation ----
    "Fancoil to WSHP(short term)":                         "boiler",
    "MUA Hydronic Conversion":              "mua",
    "MUA Hydronic + BAS + VFD":             "mua",
    "MUA VFD Retrofit":                     "mua",
    "Packaged Heating/Cooling MUA":         "mua",
    "Upper MUA Hydronic Conversion":        "mua",
    "Solar Preheat – Upper MUA":            "mua",
    "Roof MUA Heat Recovery":               "mua",
    "Replace the existing Makeup Air Unit (MUA) with a packaged heating and cooling MUA": "mua",
    "Convert Upper MUA to Hydronic Heating Connected to Common Area Boiler": "mua",
    "Install Heat Recovery Ventilation System for Roof MUA and Exhaust Fans": "mua",

    # ---- Hydronic Loops ----
    "Primary–Secondary Boiler and DHW Piping": "loop",
    "Primary-Secondary Boiler and DHW Piping": "loop",
    "Combine the Existing Hydronic system into Primary - Secondary Loops to Provide Sufficient Space Heating and Save Energy": "loop",

    # ---- Lighting ----
    "Common Area Lighting Retrofit":        "lighting",
    "Motion Sensor for Lighting Retrofit for Common Area Lighting": "lighting",

    # ---- Building Envelope ----
    "Window Striping (Caulking) Upgrade":   "envelope",
    "Windows Retrofit":                     "envelope",
    "Window Striping (Caulking) Upgrade":   "envelope",

    # ---- Water & DHW ----
    "Enbridge Gas Boiler Optimization Pilot Program": "boiler",
    "Solar Preheat – DHW":                  "water",
    "DHW retrofit + plate and frame HX + mixing valve": "water",

    # ---- Pumps / Power / PF ----
    "Cooling Tower Fan VFD":                "pumps",
    "Booster Pump VFD":                     "pumps",
    "Install VFD on Cooling Tower Fan":     "pumps",
    "Install VFDs on Booster Pumps":        "pumps",
    "Install Power Factor Correction Devices": "pumps",

    # ---- Other / Misc ----
    "Investigate Electric Heating":         "other",
    "EV Charging Stations":                 "other",
    "Gas Co-Generation (CHP)":              "other",
    "Fan Coil to WSHP":                     "other",
    "Fan Coil Unit Retrofit":               "other",
    "Dry-O-Tron Pool Unit":                 "other",
    "Replace the Pool Exhaust Fan and AHU with Dry-O-Tron Unit": "other",
    "Garage CO Sensors":                    "other",
    "Adding a Heat Exchanger to Isolate the Glycol Tower Loop from the Building Loop":               "loop",
    "Misc Maintenance Upgrades":            "other",
    "Geothermal Upgrade":                   "other",
    "Separate Garage Exhaust Fans from Cooling Tower Well": "other",
    "Re-commissioning  of HVAC (Heating) Equipment": "other",
    # 其余没写到的 key 会自动归到 "Other / Misc"
}


# 样式名：按你 Word 模板实际样式名称修改
STYLE_MEASURE_TITLE = "heanding 2"  # 这是你模板里的名字就行
STYLE_SECTION_SUB   = "Normal"
STYLE_BODY          = "Normal"

DEFAULT_MEASURE_TEMPLATES = {key: dict(value) for key, value in MEASURE_TEMPLATES.items()}
DEFAULT_CATEGORIES = list(CATEGORIES)
DEFAULT_CATEGORY_BY_MEASURE = dict(CATEGORY_BY_MEASURE)
DEFAULT_STYLES = {
    "measure_title_style": STYLE_MEASURE_TITLE,
    "section_subtitle_style": STYLE_SECTION_SUB,
    "body_style": STYLE_BODY,
}

DEFAULT_PLACEHOLDERS = {
    "measure_block_paragraph": "{MEASURE_BLOCK}",
    "measure_summary_table_row": "{MEASURE_SUMMARY_ROW}",
}
FINDINGS_PLACEHOLDER = "{FINDINGS_BLOCK}"
DEFAULT_SECTION_HEADINGS = {
    "existing_conditions_heading": "Existing Conditions",
    "retrofit_conditions_heading": "Retrofit Conditions",
}
DEFAULT_PAGINATION = {
    "page_break_between_measures": True,
    "no_page_break_after_last_measure": True,
}

DEFAULT_TEMPLATE_JSON_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "templates",
    "template.level1.json",
)


def load_level1_template(json_path):
    with open(json_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    for key in ("word_template_requirements", "ui_categories", "measures"):
        if key not in data:
            raise ValueError(f"Missing required field: {key}")

    requirements = data["word_template_requirements"]
    placeholders = requirements.get("docx_placeholders")
    styles = requirements.get("styles")
    section_headings = requirements.get("section_headings")
    pagination = requirements.get("pagination", {})

    if not isinstance(placeholders, dict):
        raise ValueError("Missing docx_placeholders configuration.")
    if not isinstance(styles, dict):
        raise ValueError("Missing styles configuration.")
    if not isinstance(section_headings, dict):
        raise ValueError("Missing section_headings configuration.")

    for key in ("measure_block_paragraph", "measure_summary_table_row"):
        if key not in placeholders:
            raise ValueError(f"Missing placeholder: {key}")
    for key in ("measure_title_style", "section_subtitle_style", "body_style"):
        if key not in styles:
            raise ValueError(f"Missing style definition: {key}")
    for key in ("existing_conditions_heading", "retrofit_conditions_heading"):
        if key not in section_headings:
            raise ValueError(f"Missing section heading: {key}")

    measures = {}
    for key, measure in data["measures"].items():
        if not isinstance(measure, dict):
            raise ValueError(f"Invalid measure definition for {key}")
        for field in ("category", "name", "existing", "retrofit"):
            if field not in measure:
                raise ValueError(f"Measure {key} missing field: {field}")
        measures[key] = {
            "category": measure["category"],
            "name": measure["name"],
            "summary": measure.get("summary", ""),
            "existing": measure["existing"],
            "retrofit": measure["retrofit"],
        }

    categories = []
    for item in data["ui_categories"]:
        if not isinstance(item, dict) or "tab_title" not in item or "code" not in item:
            raise ValueError("Invalid ui_categories entry.")
        categories.append((item["tab_title"], item["code"]))

    category_by_measure = {key: measure["category"] for key, measure in measures.items()}
    overrides = data.get("category_by_measure_overrides", {})
    if overrides:
        if not isinstance(overrides, dict):
            raise ValueError("category_by_measure_overrides must be a mapping.")
        category_by_measure.update(overrides)

    checklists = data.get("checklists", {})
    if checklists is None:
        checklists = {}
    if not isinstance(checklists, dict):
        raise ValueError("checklists must be a mapping if provided.")

    return {
        "measures": measures,
        "categories": categories,
        "category_by_measure": category_by_measure,
        "styles": styles,
        "placeholders": placeholders,
        "section_headings": section_headings,
        "pagination": pagination,
        "checklists": checklists,
    }


def _load_fallback_template_config():
    return {
        "measures": {key: dict(value) for key, value in DEFAULT_MEASURE_TEMPLATES.items()},
        "categories": list(DEFAULT_CATEGORIES),
        "category_by_measure": dict(DEFAULT_CATEGORY_BY_MEASURE),
        "styles": dict(DEFAULT_STYLES),
        "placeholders": dict(DEFAULT_PLACEHOLDERS),
        "section_headings": dict(DEFAULT_SECTION_HEADINGS),
        "pagination": dict(DEFAULT_PAGINATION),
        "checklists": {},
    }


try:
    _TEMPLATE_CONFIG = load_level1_template(DEFAULT_TEMPLATE_JSON_PATH)
except (OSError, ValueError, json.JSONDecodeError):
    _TEMPLATE_CONFIG = _load_fallback_template_config()

MEASURE_TEMPLATES = _TEMPLATE_CONFIG["measures"]
CATEGORIES = _TEMPLATE_CONFIG["categories"]
CATEGORY_BY_MEASURE = _TEMPLATE_CONFIG["category_by_measure"]
PLACEHOLDERS = _TEMPLATE_CONFIG["placeholders"]
SECTION_HEADINGS = _TEMPLATE_CONFIG["section_headings"]
PAGINATION = _TEMPLATE_CONFIG["pagination"]
STYLE_MEASURE_TITLE = _TEMPLATE_CONFIG["styles"].get("measure_title_style", STYLE_MEASURE_TITLE)
STYLE_SECTION_SUB = _TEMPLATE_CONFIG["styles"].get("section_subtitle_style", STYLE_SECTION_SUB)
STYLE_BODY = _TEMPLATE_CONFIG["styles"].get("body_style", STYLE_BODY)
CHECKLIST_SELECTIONS = {}


# -------------------- Word helpers -------------------- #
def add_paragraph_after(paragraph, text="", style=None, bold=False):
    """
    在给定 paragraph 后面插入一个新段落并返回它。
    方便我们按顺序往下写，不用做倒序插入。
    """
    new_p_elm = OxmlElement("w:p")
    paragraph._element.addnext(new_p_elm)
    new_p = Paragraph(new_p_elm, paragraph._parent)

    if style:
        new_p.style = style

    if text:
        run = new_p.add_run(text)
        if bold:
            run.bold = True
    else:
        # 没有文字但需要加粗其实没意义，这里就不处理 bold 了
        pass

    return new_p


def add_paragraph_after_safe(paragraph, text="", style=None, bold=False):
    new_p = add_paragraph_after(paragraph, text, None, bold)
    if style:
        try:
            new_p.style = style
        except KeyError:
            pass
    return new_p

#-----------填 summary 表格的函数-------------------#
def fill_measure_summary_table(doc, selected_keys):
    """
    在 Word 模板里找到包含 {MEASURE_SUMMARY_ROW} 的那一行，
    用选中的 measures 填充 summary 表格。

    假设：
    - 这一行所在表格有两列：
        第 1 列：Description of Measure
        第 2 列：Estimated Utility / Cost Savings
    - 这一行的第 1 个单元格内容是 {MEASURE_SUMMARY_ROW}
    """
    placeholder = PLACEHOLDERS.get(
        "measure_summary_table_row",
        DEFAULT_PLACEHOLDERS["measure_summary_table_row"],
    )
    target_table = None
    target_row = None

    # 找到带占位符的那一行
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if placeholder in cell.text:
                    target_table = table
                    target_row = row
                    break
            if target_row is not None:
                break
        if target_row is not None:
            break

    # 如果模板里没有这个表格，就直接跳过，不报错
    if target_row is None or target_table is None:
        return

    # 如果没有选 measure，就把这一行清空
    if not selected_keys:
        for cell in target_row.cells:
            cell.text = ""
        return

    first = True
    for key in selected_keys:
        tpl = MEASURE_TEMPLATES[key]
        name = tpl.get("name", key)
        summary = tpl.get("summary", "")

        if first:
            row = target_row
            first = False
        else:
            row = target_table.add_row()

        # 假设表格只有两列；如果有第三列可以在这里加
        row.cells[0].text = name
        row.cells[1].text = summary

    # 确保占位符被清掉
    if placeholder in row.cells[0].text:
        row.cells[0].text = row.cells[0].text.replace(placeholder, "")

# -------------------- Measure insert -------------------- #
def insert_measures_into_docx(template_path, output_path, selected_keys):
    """
    在 template_path 的 docx 中寻找 {MEASURE_BLOCK} 所在段落，
    按顺序把选中的 measures 写进去，然后保存到 output_path。
    - 标题用 STYLE_MEASURE_TITLE
    - Existing / Retrofit 副标题用 STYLE_SECTION_SUB 并加粗
    - 正文用 STYLE_BODY
    - 每个 measure 的最后插一个分页符（下一条新起一页），最后一条不分页
    """
    if not selected_keys:
        raise ValueError("No measures selected.")

    doc = Document(template_path)

    # 先填 introduction 里的 measure summary 表格
    fill_measure_summary_table(doc, selected_keys)

    # 1. 找到占位符段落
    placeholder = PLACEHOLDERS.get(
        "measure_block_paragraph",
        DEFAULT_PLACEHOLDERS["measure_block_paragraph"],
    )
    anchor_idx = None
    for i, para in enumerate(doc.paragraphs):
        if placeholder in para.text:
            anchor_idx = i
            break

    if anchor_idx is None:
        raise RuntimeError("Placeholder {MEASURE_BLOCK} not found in template.")

    anchor_para = doc.paragraphs[anchor_idx]

    # 把占位符清空，等会儿拿来当“第一条 measure 的标题段”
    anchor_para.text = ""
    if STYLE_MEASURE_TITLE:
        anchor_para.style = STYLE_MEASURE_TITLE

    current_para = anchor_para
    total = len(selected_keys)

    # 2. 按顺序写每一个 measure
    for idx, key in enumerate(selected_keys, start=1):
        tpl = MEASURE_TEMPLATES[key]

        # ---------- 2.1 标题：3.x Measure – Name ----------
        title_text = f"3.{idx} Measure – {tpl['name']}"
        if idx == 1:
            # 第一条直接写在 anchor_para 上
            run_title = current_para.add_run(title_text)
        else:
            current_para = add_paragraph_after(current_para, "", STYLE_BODY)
            current_para = add_paragraph_after(current_para, title_text, STYLE_MEASURE_TITLE)
            run_title = current_para.runs[0]

        # 这里标题是否加粗你自己决定，我先不加粗
        # run_title.bold = True

        # ---------- 2.2 Existing Conditions 小标题 ----------
        exist_heading = SECTION_HEADINGS.get(
            "existing_conditions_heading",
            DEFAULT_SECTION_HEADINGS["existing_conditions_heading"],
        )
        exist_sub = add_paragraph_after(
            current_para,
            exist_heading,
            STYLE_SECTION_SUB,
            bold=True
        )

        # ---------- 2.3 Existing Conditions 正文 ----------
        exist_body = add_paragraph_after(
            exist_sub,
            tpl["existing"],
            STYLE_BODY,
            bold=False
        )

        # 空一行
        blank1 = add_paragraph_after(exist_body, "", STYLE_BODY)

        # ---------- 2.4 Retrofit Conditions 小标题 ----------
        retrofit_heading = SECTION_HEADINGS.get(
            "retrofit_conditions_heading",
            DEFAULT_SECTION_HEADINGS["retrofit_conditions_heading"],
        )
        retro_sub = add_paragraph_after(
            blank1,
            retrofit_heading,
            STYLE_SECTION_SUB,
            bold=True
        )

        # ---------- 2.5 Retrofit Conditions 正文 ----------
        retro_body = add_paragraph_after(
            retro_sub,
            tpl["retrofit"],
            STYLE_BODY,
            bold=False
        )

        # measure 结束后的空行
        end_blank = add_paragraph_after(retro_body, "", STYLE_BODY)
        current_para = end_blank

        # ---------- 2.6 除最后一条外，插入分页符 ----------
        should_page_break = PAGINATION.get("page_break_between_measures", True)
        no_break_after_last = PAGINATION.get("no_page_break_after_last_measure", True)
        if should_page_break and not (no_break_after_last and idx == total):
            pb_para = add_paragraph_after(current_para, "", STYLE_BODY)
            run_pb = pb_para.add_run()
            run_pb.add_break(WD_BREAK.PAGE)
            current_para = pb_para

    # 3. 保存
    insert_findings_into_docx(doc, CHECKLIST_SELECTIONS)
    doc.save(output_path)


def insert_findings_into_docx(doc, findings, placeholder=FINDINGS_PLACEHOLDER):
    if not findings:
        return

    anchor_para = None
    for para in doc.paragraphs:
        if para.text == placeholder:
            anchor_para = para
            break

    if anchor_para is None:
        anchor_para = doc.add_paragraph("")
    else:
        anchor_para.text = ""

    current_para = anchor_para
    first_group = True

    for group_name, categories in findings.items():
        if not isinstance(categories, dict):
            continue

        if first_group:
            if STYLE_MEASURE_TITLE:
                try:
                    current_para.style = STYLE_MEASURE_TITLE
                except KeyError:
                    pass
            current_para.add_run(group_name)
            first_group = False
        else:
            current_para = add_paragraph_after_safe(current_para, "", STYLE_BODY)
            current_para = add_paragraph_after_safe(current_para, group_name, STYLE_MEASURE_TITLE)

        for category_name, items in categories.items():
            if not items or not isinstance(items, list):
                continue
            category_para = add_paragraph_after_safe(
                current_para,
                category_name,
                STYLE_SECTION_SUB,
                bold=True,
            )
            current_para = category_para
            for item in items:
                bullet_para = add_paragraph_after_safe(
                    current_para,
                    item,
                    "List Bullet",
                )
                current_para = bullet_para

        current_para = add_paragraph_after_safe(current_para, "", STYLE_BODY)



# -------------------- GUI Application -------------------- #

class MeasureToWordApp:
    def __init__(self, root):
        self.root = root
        root.title("Measure → Word Report Generator")
        root.geometry("800x500")

        self.template_path = tk.StringVar()
        self.output_path = tk.StringVar()

        # 上：模板选择
        top = ttk.Frame(root, padding=8)
        top.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top, text="Word Template:").pack(side=tk.LEFT)
        ttk.Entry(top, textvariable=self.template_path, width=60).pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="Browse...", command=self.browse_template).pack(side=tk.LEFT)

        # 中：左边 measure 选择，右边预览
        # 中：左边 measure 选择（分 TAB），右边预览
        main = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # 左侧整体 panel（里面上半 Notebook，下半按钮）
        left_panel = ttk.Frame(main)
        main.add(left_panel, weight=1)

        # --- Notebook: 按类别分 TAB ---
        nb = ttk.Notebook(left_panel)
        nb.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # 每个类别一个 frame
        self.measure_vars = {}
        tab_frames = {}
        row_index_by_cat = {}

        for tab_title, cat_code in CATEGORIES:
            frame = ttk.Labelframe(nb, text=tab_title)
            nb.add(frame, text=tab_title)
            tab_frames[cat_code] = frame
            row_index_by_cat[cat_code] = 0

        # 把每个 measure 放进对应的 tab（不在映射里的归到 "other"）
        for key in MEASURE_TEMPLATES.keys():
            cat_code = CATEGORY_BY_MEASURE.get(key, "other")
            frame = tab_frames.get(cat_code, tab_frames["other"])

            row = row_index_by_cat[cat_code]
            var = tk.BooleanVar(value=False)
            self.measure_vars[key] = var
            ttk.Checkbutton(frame, text=key, variable=var).grid(
                row=row, column=0, sticky="w", padx=4, pady=2
            )
            row_index_by_cat[cat_code] += 1

        # --- 下方：Select All / Clear 按钮（对全部 measure 生效）---
        btn_frame = ttk.Frame(left_panel)
        btn_frame.pack(side=tk.BOTTOM, anchor="w", pady=(5, 0))
        ttk.Button(btn_frame, text="Select All", command=self.select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Clear", command=self.clear_all).pack(side=tk.LEFT, padx=2)

        # 右侧预览保持原样
        right = ttk.Labelframe(main, text="Preview (plain text)")
        main.add(right, weight=2)

        self.preview_text = tk.Text(right, wrap="word")
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)


        

        # 下：生成按钮
        bottom = ttk.Frame(root, padding=8)
        bottom.pack(side=tk.BOTTOM, fill=tk.X)

        ttk.Button(bottom, text="Preview Text", command=self.update_preview).pack(side=tk.LEFT)
        ttk.Button(bottom, text="Generate Word Report", command=self.generate_word).pack(side=tk.RIGHT)

    # ------ UI helpers ------ #

    def browse_template(self):
        path = filedialog.askopenfilename(
            title="Select Word Template",
            filetypes=[("Word files", "*.docx"), ("All files", "*.*")]
        )
        if path:
            self.template_path.set(path)

    def select_all(self):
        for v in self.measure_vars.values():
            v.set(True)

    def clear_all(self):
        for v in self.measure_vars.values():
            v.set(False)

    def get_selected_keys(self):
        return [k for k, v in self.measure_vars.items() if v.get()]

    # ------ Preview / Generate ------ #

    def update_preview(self):
        self.preview_text.delete("1.0", tk.END)
        selected = self.get_selected_keys()
        if not selected:
            self.preview_text.insert(tk.END, "No measures selected.\n")
            return

        existing_heading = SECTION_HEADINGS.get(
            "existing_conditions_heading",
            DEFAULT_SECTION_HEADINGS["existing_conditions_heading"],
        )
        retrofit_heading = SECTION_HEADINGS.get(
            "retrofit_conditions_heading",
            DEFAULT_SECTION_HEADINGS["retrofit_conditions_heading"],
        )

        idx = 1
        for key in selected:
            tpl = MEASURE_TEMPLATES[key]
            self.preview_text.insert(tk.END, f"3.{idx} Measure – {tpl['name']}\n\n")
            self.preview_text.insert(tk.END, f"{existing_heading}\n")
            self.preview_text.insert(tk.END, tpl["existing"] + "\n\n")
            self.preview_text.insert(tk.END, f"{retrofit_heading}\n")
            self.preview_text.insert(tk.END, tpl["retrofit"] + "\n\n")
            self.preview_text.insert(tk.END, "-" * 70 + "\n\n")
            idx += 1

    def generate_word(self):
        template = self.template_path.get().strip()
        if not template:
            messagebox.showerror("Error", "Please select a Word template first.")
            return
        if not os.path.exists(template):
            messagebox.showerror("Error", "Template file not found.")
            return

        selected = self.get_selected_keys()
        if not selected:
            messagebox.showerror("Error", "Please select at least one measure.")
            return

        out_path = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Word files", "*.docx")],
            title="Save generated report as"
        )
        if not out_path:
            return

        try:
            insert_measures_into_docx(template, out_path, selected)
            messagebox.showinfo("Success", f"Report generated:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass

    app = MeasureToWordApp(root)
    root.mainloop()



def generate_level1_report(
    project_json_path: str,
    template_json_path: str,
    docx_template_path: str,
    out_path: str,
) -> str:
    """
    Headless entrypoint (no Tkinter).
    Loads project.json + template.level1.json,
    resolves selected_measures, and calls insert_measures_into_docx.
    Returns out_path.
    """
    with open(project_json_path, "r", encoding="utf-8") as handle:
        project_data = json.load(handle)

    selected_measures = project_data.get("selected_measures")
    if not isinstance(selected_measures, list):
        raise ValueError("project.json must contain a selected_measures list.")

    template_config = load_level1_template(template_json_path)

    global MEASURE_TEMPLATES, CATEGORIES, CATEGORY_BY_MEASURE, PLACEHOLDERS
    global SECTION_HEADINGS, PAGINATION, STYLE_MEASURE_TITLE, STYLE_SECTION_SUB, STYLE_BODY
    global CHECKLIST_SELECTIONS

    MEASURE_TEMPLATES = template_config["measures"]
    CATEGORIES = template_config["categories"]
    CATEGORY_BY_MEASURE = template_config["category_by_measure"]
    PLACEHOLDERS = template_config["placeholders"]
    SECTION_HEADINGS = template_config["section_headings"]
    PAGINATION = template_config["pagination"]
    STYLE_MEASURE_TITLE = template_config["styles"].get("measure_title_style", STYLE_MEASURE_TITLE)
    STYLE_SECTION_SUB = template_config["styles"].get("section_subtitle_style", STYLE_SECTION_SUB)
    STYLE_BODY = template_config["styles"].get("body_style", STYLE_BODY)
    CHECKLIST_SELECTIONS = project_data.get("checklist_selections") or {}

    insert_measures_into_docx(docx_template_path, out_path, selected_measures)
    return out_path

