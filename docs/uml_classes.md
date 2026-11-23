# Diagramme UML des classes

GitHub affiche ce diagramme directement (bloc Mermaid).

```mermaid
classDiagram
    direction LR

    class Vector2D {
        +float x
        +float y
        +distance_to(other) float
    }

    class Dilemma {
        +str title
        +str description
        +list options
    }

    class Aircraft {
        +str callsign
        +Vector2D position
        +float heading
        +float target_heading
        +float altitude
        +float target_altitude
        +float speed
        +float target_speed
        +float fuel
        +bool is_emergency
        +bool is_landed
        +bool has_crashed
        +Dilemma pending_dilemma
        +bool dilemma_resolved
        -_generate_random_dilemma() Dilemma
        +update(dt)
    }

    class AirspaceManager {
        +List~Aircraft~ aircrafts
        +Vector2D runway_pos
        +int money
        +int score
        +int landed_count
        +int collisions_count
        +int radar_level
        +int radar_radius
        +int radar_upgrade_cost
        +float scan_angle
        +upgrade_radar() bool
        +spawn_aircraft()
        +update(dt)
        -_check_collisions()
        -_check_landings()
        -_clean_up()
    }

    class AssetManager {
        +get_airplane_sprite()$ QPixmap
        +get_runway_texture()$ QPixmap
    }

    class RadarWidget {
        +AirspaceManager manager
        +str selected_callsign
        +aircraft_selected Signal
        +mousePressEvent(event)
        +paintEvent(event)
        -_get_scale_factor() float
        -_draw_aircraft(...)
    }

    class DilemmaDialog {
        +Dilemma dilemma
        +int selected_option_idx
        +accept_choice()
    }

    class MainWindow {
        +AirspaceManager manager
        +RadarWidget radar
        +QTimer timer
        +game_loop()
        +send_instruction(action)
        +open_dilemma_modal()
        +buy_radar_upgrade()
        +update_control_panel()
        +sync_aircraft_list()
    }

    QObject <|-- AirspaceManager
    QWidget <|-- RadarWidget
    QDialog <|-- DilemmaDialog
    QMainWindow <|-- MainWindow

    AirspaceManager "1" *-- "0..25" Aircraft : gère
    Aircraft "1" *-- "1" Vector2D : position
    Aircraft "1" o-- "0..1" Dilemma : urgence
    AirspaceManager --> Vector2D : piste
    MainWindow *-- AirspaceManager
    MainWindow *-- RadarWidget
    MainWindow ..> DilemmaDialog : ouvre
    RadarWidget --> AirspaceManager : lit
    RadarWidget ..> AssetManager : sprites
    DilemmaDialog --> Dilemma : affiche
```

## Répartition dans main.py

| Partie de main.py | Classes | Responsable |
| --- | --- | --- |
| 0 | AssetManager | Personne A (interface) |
| 1 | Vector2D, Dilemma, Aircraft, AirspaceManager | Personne B (fonctionnement) |
| 2, 3, 4 | DilemmaDialog, RadarWidget, MainWindow | Personne A (interface) |
