```mermaid
flowchart TB
    %% Client Applications
    subgraph VictimClients["Victim Applications"]
        style VictimClients fill:#0D1117,stroke:#FF3366,color:#FF3366
        
        subgraph VMobile["Victim Mobile App"]
            style VMobile fill:#161B22,stroke:#FF3366,color:#FF3366
            VMA["Mobile App\n(React Native)"]
            subgraph VMobileFeatures["Features"]
                style VMobileFeatures fill:#1C2128,stroke:#FF3366,color:#FF3366
                VSOS["Emergency SOS"]
                VLoc["Location Tracking"]
                VChat["Emergency Chat"]
                VStatus["Status Updates"]
            end
        end

        subgraph VWeb["Victim Web App"]
            style VWeb fill:#161B22,stroke:#4DFFD2,color:#4DFFD2
            VWA["Web App\n(React)"]
            subgraph VWebFeatures["Features"]
                style VWebFeatures fill:#1C2128,stroke:#4DFFD2,color:#4DFFD2
                VReport["Report Incident"]
                VHistory["Case History"]
                VResources["Resource Access"]
            end
        end
    end

    subgraph RescueClients["Rescue Team Applications"]
        style RescueClients fill:#0D1117,stroke:#00FFFF,color:#00FFFF
        
        subgraph RMobile["Rescue Mobile App"]
            style RMobile fill:#161B22,stroke:#00FFFF,color:#00FFFF
            RMA["Mobile App\n(React Native)"]
            subgraph RMobileFeatures["Features"]
                style RMobileFeatures fill:#1C2128,stroke:#00FFFF,color:#00FFFF
                RNav["Navigation"]
                RComm["Team Comms"]
                RCases["Active Cases"]
                REquip["Equipment Status"]
            end
        end

        subgraph RWeb["Rescue Web App"]
            style RWeb fill:#161B22,stroke:#4DFFD2,color:#4DFFD2
            RWA["Web App\n(React)"]
            subgraph RWebFeatures["Features"]
                style RWebFeatures fill:#1C2128,stroke:#4DFFD2,color:#4DFFD2
                RDash["Responder Dashboard"]
                RReports["Mission Reports"]
                RTeam["Team Management"]
            end
        end
    end

    subgraph HQSystem["HQ Command Center"]
        style HQSystem fill:#0D1117,stroke:#FF1493,color:#FF1493
        
        subgraph HQWeb["HQ Web Platform"]
            style HQWeb fill:#161B22,stroke:#FF1493,color:#FF1493
            HQA["Admin Portal\n(React + Streamlit)"]
            subgraph HQFeatures["Features"]
                style HQFeatures fill:#1C2128,stroke:#FF1493,color:#FF1493
                HQDash["Command Dashboard"]
                HQDisp["Dispatch Control"]
                HQAnalytics["Analytics Center"]
                HQRes["Resource Management"]
            end
        end
    end

    subgraph Backend["Backend Services"]
        style Backend fill:#0D1117,stroke:#4DFFD2,color:#4DFFD2
        
        subgraph Core["Core Services"]
            style Core fill:#161B22,stroke:#4DFFD2,color:#4DFFD2
            Auth["Authentication"]
            IncidentMgmt["Incident Management"]
            ResourceMgmt["Resource Management"]
            CommSystem["Communication System"]
        end

        subgraph RealTime["Real-time Services"]
            style RealTime fill:#161B22,stroke:#00FFFF,color:#00FFFF
            LocationTrack["Location Tracking"]
            Notifications["Alert System"]
            LiveChat["Chat Service"]
        end

        subgraph DataServices["Data Services"]
            style DataServices fill:#161B22,stroke:#FF1493,color:#FF1493
            Analytics["Analytics Engine"]
            Reporting["Report Generation"]
            ML["ML Predictions"]
        end
    end

    subgraph Infrastructure["Infrastructure Layer"]
        style Infrastructure fill:#0D1117,stroke:#00FFFF,color:#00FFFF
        
        subgraph Data["Data Storage"]
            style Data fill:#161B22,stroke:#00FFFF,color:#00FFFF
            DB[(Main Database)]
            Cache[(Redis Cache)]
            GIS[(GIS Data)]
        end

        subgraph Queue["Message Queues"]
            style Queue fill:#161B22,stroke:#4DFFD2,color:#4DFFD2
            MQ[["Event Queue"]]
            NotifQ[["Notification Queue"]]
        end
    end

    %% Client to Backend Connections
    VMobile ==>|"REST/WS"| Core
    VWeb ==>|"REST/WS"| Core
    RMobile ==>|"REST/WS"| Core
    RWeb ==>|"REST/WS"| Core
    HQWeb ==>|"REST/WS"| Core

    %% Real-time Connections
    VMA -.->|"WebSocket"| RealTime
    RMA -.->|"WebSocket"| RealTime
    HQA -.->|"WebSocket"| RealTime

    %% Backend Internal Flows
    Core ==>|"Process"| DataServices
    RealTime ==>|"Events"| Queue
    DataServices ==>|"Query"| Data

    %% Cross-functional Flows
    VSOS -->|"Emergency"| Notifications
    VLoc -->|"GPS"| LocationTrack
    RNav -->|"Routes"| GIS
    HQDash -->|"Overview"| Analytics

    %% Critical Paths
    VSOS ==>|"Priority"| IncidentMgmt
    IncidentMgmt ==>|"Dispatch"| RCases
    RCases ==>|"Updates"| HQDash

    classDef default fill:#161B22,stroke:#4DFFD2,color:#4DFFD2

    %% Connection Styling
    linkStyle default stroke:#4DFFD2,stroke-width:2px
'''
