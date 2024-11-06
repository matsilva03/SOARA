from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
import pandas as pd
from pulp import *

class RoomType(Enum):
    LAB = 'lab'
    CLASSROOM = 'sala'

@dataclass
class Course:
    name: str
    course_code: str
    day: str
    time: str
    class_size: int
    requires_lab: bool
    preferred_floor: int
    floor_preference_weight: float = 1.0
    time_slots: List[int] = None
    split_authorized: bool = False
    assigned_professors: List[str] = None
    is_split: bool = False

    def __post_init__(self):
        self.time_slots = TimeSlotManager.create_time_slots(self.day, self.time)
        if self.assigned_professors is None:
            self.assigned_professors = []

    def can_be_split(self) -> bool:
        """Check if the course meets all criteria for splitting"""
        return (
            self.class_size > 50 and
            self.split_authorized and
            len(self.assigned_professors) >= 2
        )

@dataclass
class Room:
    name: str
    room_type: RoomType
    capacity: int
    floor: int
    is_blocked: bool = False
    floor_matches: Dict[str, int] = None

    def __post_init__(self):
        self.floor_matches = {}

class TimeSlotManager:
    DAY_TO_BASE_INDEX = {
        "Segunda": 0, "Terça": 8, "Quarta": 16,
        "Quinta": 24, "Sexta": 32, "Sábado": 40
    }

    TIME_TO_INDEX = {
        "17h20": 0, "18h10": 1, "19h00": 2, "19h50": 3,
        "20h50": 4, "21h40": 5, "22h30": 6
    }

    @classmethod
    def create_time_slots(cls, day: str, time_range: str) -> List[int]:
        time_slots = [0] * 48
        start_time, end_time = time_range.split('-')

        base_idx = cls.DAY_TO_BASE_INDEX.get(day, 0)
        start_idx = base_idx + cls.TIME_TO_INDEX.get(start_time, 0)

        slots_needed = 4 if time_range == "19h00-22h30" else 2

        for i in range(start_idx, start_idx + slots_needed):
            if i < len(time_slots):
                time_slots[i] = 1
  
        return time_slots

    @staticmethod
    def has_conflict(slots1: List[int], slots2: List[int]) -> bool:
        return any(s1 and s2 for s1, s2 in zip(slots1, slots2))

class DataLoader:
    @staticmethod
    def load_data(courses_file: str, rooms_file: str) -> Tuple[List[Course], List[Room]]:
        courses_df = pd.read_csv(courses_file)
        rooms_df = pd.read_csv(rooms_file)

        courses = []
        for _, row in courses_df.iterrows():
            professors = row.get('assigned_professors', '').split(',') if pd.notna(row.get('assigned_professors')) else []
            professors = [p.strip() for p in professors if p.strip()]

            course = Course(
                name=row['name'],
                course_code=row['course'],
                day=row['day'],
                time=row['time'],
                class_size=row['class_size'],
                requires_lab=row['req'] == 1,
                preferred_floor=row['pref_floor'],
                floor_preference_weight=row.get('course_floor_pref', 1),
                split_authorized=row.get('split_authorized', False),
                assigned_professors=professors
            )

            if course.can_be_split():
                split1 = Course(
                    name=f"{course.name} (Turma A)",
                    course_code=f"{course.course_code}-A",
                    day=course.day,
                    time=course.time,
                    class_size=course.class_size // 2,
                    requires_lab=course.requires_lab,
                    preferred_floor=course.preferred_floor,
                    floor_preference_weight=course.floor_preference_weight,
                    split_authorized=True,
                    assigned_professors=[course.assigned_professors[0]],
                    is_split=True
                )

                split2 = Course(
                    name=f"{course.name} (Turma B)",
                    course_code=f"{course.course_code}-B",
                    day=course.day,
                    time=course.time,
                    class_size=course.class_size - (course.class_size // 2),
                    requires_lab=course.requires_lab,
                    preferred_floor=course.preferred_floor,
                    floor_preference_weight=course.floor_preference_weight,
                    split_authorized=True,
                    assigned_professors=[course.assigned_professors[1]],
                    is_split=True
                )

                courses.extend([split1, split2])
            else:
                courses.append(course)

        rooms = [
            Room(
                name=row['name'],
                room_type=RoomType(row['type'].lower()),
                capacity=row['capacity'],
                floor=row['floor'],
                is_blocked=row.get('is_blocked', False)
            )
            for _, row in rooms_df.iterrows()
        ]
        
        return courses, rooms

class ScheduleOptimizer:
    def __init__(self, courses: List[Course], rooms: List[Room]):
        self.courses = courses
        self.rooms = rooms
        self.weights = {
            'floor_pref': 10,
            'lab_usage': 5,
            'wrong_room': 20,
            'distance': 2,
            'capacity_penalty': 15
        }
        self.model = None
        self.variables = {}
        self._calculate_floor_matches()

    def _calculate_floor_matches(self):
        for room in self.rooms:
            for course in self.courses:
                if course.preferred_floor <= 0:
                    room.floor_matches[course.name] = 1
                else:
                    room.floor_matches[course.name] = 1 if room.floor == course.preferred_floor else 0

    def optimize(self) -> pd.DataFrame:
        self.model = self._create_model()
        status = self.model.solve()

        if status == LpStatusOptimal:
            return self._format_results()
        return pd.DataFrame()

    def _create_model(self) -> LpProblem:
        model = LpProblem("Classroom_Assignment", LpMinimize)

        self.variables = self._create_decision_variables()

        constraints = self._create_constraints()
        for constraint in constraints:
            model += constraint

        model += self._create_objective_function()

        return model

    def _create_decision_variables(self) -> Dict:
        """Create and return all decision variables for the optimization model."""
        variables = {}

        variables['x'] = LpVariable.dicts(
            "assign",
            ((d, r) for d in range(len(self.courses)) for r in range(len(self.rooms))),
            cat='Binary'
        )

        variables['y'] = LpVariable.dicts(
            "distance",
            (d for d in range(len(self.courses))),
            lowBound=0,
            cat='Integer'
        )

        variables['z'] = LpVariable.dicts(
            "capacity_violation",
            ((d, r) for d in range(len(self.courses)) for r in range(len(self.rooms))),
            lowBound=0,
            cat='Integer'
        )

        variables['w_lab'] = LpVariable.dicts(
            "wrong_lab_usage",
            (d for d in range(len(self.courses))),
            cat='Binary'
        )

        variables['w_sala'] = LpVariable.dicts(
            "wrong_sala_usage",
            (d for d in range(len(self.courses))),
            cat='Binary'
        )

        return variables

    def _create_constraints(self) -> List[LpConstraint]:
        """Create and return all constraints for the optimization model."""
        constraints = []
        x = self.variables['x']
        w_lab = self.variables['w_lab']
        w_sala = self.variables['w_sala']
        y = self.variables['y']
        z = self.variables['z']

        # Each course must be assigned to exactly one room
        for d in range(len(self.courses)):
            constraints.append(
                lpSum(x[d,r] for r in range(len(self.rooms))) == 1
            )

        # Time slot conflicts
        for r in range(len(self.rooms)):
            for h in range(48):  # 48 time slots
                constraints.append(
                    lpSum(x[d,r] * self.courses[d].time_slots[h]
                         for d in range(len(self.courses))) <= 1
                )

        # Room type constraints
        lab_rooms = [r for r, room in enumerate(self.rooms) 
                    if room.room_type == RoomType.LAB]

        for d in range(len(self.courses)):
            if self.courses[d].requires_lab:
                constraints.append(
                    w_lab[d] == 1 - lpSum(x[d,r] for r in lab_rooms)
                )
            else:
                constraints.append(
                    w_sala[d] == lpSum(x[d,r] for r in lab_rooms)
                )

        # Distance constraints
        for d in range(len(self.courses)):
            for r in range(len(self.rooms)):
                constraints.append(
                    y[d] >= x[d,r] * abs(self.courses[d].preferred_floor - 
                                       self.rooms[r].floor)
                )

        # Capacity constraints
        for d in range(len(self.courses)):
            for r in range(len(self.rooms)):
                constraints.append(
                    z[d,r] >= x[d,r] * (self.courses[d].class_size - 
                                       self.rooms[r].capacity)
                )

                # Prevent assignments that exceed capacity by more than 20%
                constraints.append(
                    self.courses[d].class_size <= 
                    (self.rooms[r].capacity * 1.2 + (1 - x[d,r]) * 9999)
                )

        blocked_rooms = [r for r, room in enumerate(self.rooms) if room.is_blocked]
        for r in blocked_rooms:
            constraints.append(
                lpSum(x[d,r] for d in range(len(self.courses))) == 0
            )

        return constraints

    def _create_objective_function(self) -> LpAffineExpression:
        """Create and return the objective function for the optimization model."""
        x = self.variables['x']
        w_lab = self.variables['w_lab']
        w_sala = self.variables['w_sala']
        y = self.variables['y']
        z = self.variables['z']

        return (
            self.weights['floor_pref'] * lpSum(
                x[d,r] * self.courses[d].floor_preference_weight *
                (1 - self.rooms[r].floor_matches[self.courses[d].name])
                for d in range(len(self.courses))
                for r in range(len(self.rooms))
            ) +
            self.weights['lab_usage'] * lpSum(w_sala[d] 
                                            for d in range(len(self.courses))) +
            self.weights['wrong_room'] * lpSum(w_lab[d] 
                                             for d in range(len(self.courses))) +
            self.weights['distance'] * lpSum(y[d] 
                                           for d in range(len(self.courses))) +
            self.weights['capacity_penalty'] * lpSum(z[d,r]
                for d in range(len(self.courses))
                for r in range(len(self.rooms)))
        )

    def _format_results(self) -> pd.DataFrame:
        """Format optimization results into a pandas DataFrame."""
        results = []
        x = self.variables['x']

        for d in range(len(self.courses)):
            for r in range(len(self.rooms)):
                if value(x[d,r]) == 1:
                    course = self.courses[d]
                    room = self.rooms[r]

                    results.append({
                        'Curso': course.course_code,
                        'Disciplina': course.name,
                        'Sala': room.name,
                        'Dia': course.day,
                        'Horário': course.time,
                        'Andar': room.floor,
                        'Tipo Sala': room.room_type.value.upper(),
                        'Andar Preferido': course.preferred_floor,
                        'Floor Match': room.floor_matches[course.name],
                        'Tamanho Turma': course.class_size,
                        'Capacidade Sala': room.capacity,
                        'Ocupação (%)': round(course.class_size / room.capacity * 100, 1),
                        'Requer Lab': course.requires_lab,
                        'Mismatch': (course.requires_lab and room.room_type != RoomType.LAB) or
                                  (not course.requires_lab and room.room_type == RoomType.LAB)
                    })

        return pd.DataFrame(results)

class ScheduleAnalyzer:
    @staticmethod
    def analyze_schedule(schedule_df: pd.DataFrame, rooms: List[Room], courses: List[Course]):
        """
        Analyze schedule including split class information
        """
        # Add original analyses
        analysis = {
            'conflicts': ScheduleAnalyzer._check_time_conflicts(schedule_df),
            'capacity_issues': ScheduleAnalyzer._check_capacity_issues(schedule_df),
            'room_mismatches': ScheduleAnalyzer._check_room_type_mismatches(schedule_df),
            'blocked_room_usage': ScheduleAnalyzer._check_blocked_room_usage(schedule_df, rooms),
            'split_classes': ScheduleAnalyzer._analyze_split_classes(schedule_df, courses)
        }
        return analysis

    @staticmethod
    def _analyze_split_classes(schedule_df: pd.DataFrame, courses: List[Course]) -> Dict:
        """
        Analyze information about split classes
        """
        split_classes = []
        original_courses = {course.course_code.split('-')[0]: course for course in courses}

        for course_code in schedule_df['Curso'].unique():
            base_code = course_code.split('-')[0]
            if '-A' in course_code or '-B' in course_code:
                original_course = original_courses.get(base_code)
                if original_course:
                    split_classes.append({
                        'original_course': base_code,
                        'original_size': original_course.class_size,
                        'split_sections': schedule_df[schedule_df['Curso'].str.startswith(base_code)][
                            ['Curso', 'Sala', 'Tamanho Turma', 'Horário']
                        ].to_dict('records')
                    })

        return split_classes

    @staticmethod
    def _check_time_conflicts(schedule_df: pd.DataFrame) -> List[Dict]:
        conflicts = []
        for (sala, dia, horario), group in schedule_df.groupby(['Sala', 'Dia', 'Horário']):
            if len(group) > 1:
                conflicts.append({
                    'sala': sala,
                    'dia': dia,
                    'horario': horario,
                    'disciplinas': group['Disciplina'].tolist()
                })
        return conflicts

    @staticmethod
    def _check_capacity_issues(schedule_df: pd.DataFrame) -> List[Dict]:
        capacity_issues = []
        over_capacity = schedule_df[schedule_df['Tamanho Turma'] > schedule_df['Capacidade Sala']]

        for _, row in over_capacity.iterrows():
            capacity_issues.append({
                'disciplina': row['Disciplina'],
                'sala': row['Sala'],
                'tamanho_turma': row['Tamanho Turma'],
                'capacidade_sala': row['Capacidade Sala'],
                'ocupacao': row['Ocupação (%)']
            })
        return capacity_issues

    @staticmethod
    def _check_room_type_mismatches(schedule_df: pd.DataFrame) -> List[Dict]:
        mismatches = []
        incorrect_assignments = schedule_df[schedule_df['Mismatch']]

        for _, row in incorrect_assignments.iterrows():
            tipo_necessario = "laboratório" if row['Requer Lab'] else "sala regular"
            tipo_alocado = "laboratório" if row['Tipo Sala'] == 'LAB' else "sala regular"

            mismatches.append({
                'disciplina': row['Disciplina'],
                'curso': row['Curso'],
                'sala': row['Sala'],
                'tipo_necessario': tipo_necessario,
                'tipo_alocado': tipo_alocado,
                'dia': row['Dia'],
                'horario': row['Horário']
            })
        return mismatches

    @staticmethod
    def _check_blocked_room_usage(schedule_df: pd.DataFrame, rooms: List[Room]) -> List[Dict]:
        blocked_rooms = {room.name: room.is_blocked for room in rooms}
        blocked_usage = []

        for _, row in schedule_df.iterrows():
            if blocked_rooms.get(row['Sala'], False):
                blocked_usage.append({
                    'disciplina': row['Disciplina'],
                    'sala': row['Sala'],
                    'dia': row['Dia'],
                    'horario': row['Horário']
                })

        return blocked_usage

def main():
    COURSES_FILE = "./courses_data.csv"
    ROOMS_FILE = "./rooms_data.csv"

    try:
        # Load data
        courses, rooms = DataLoader.load_data(COURSES_FILE, ROOMS_FILE)

        # Create and run optimizer
        optimizer = ScheduleOptimizer(courses, rooms)
        schedule_df = optimizer.optimize()

        if not schedule_df.empty:
            # Analyze results
            analysis = ScheduleAnalyzer.analyze_schedule(schedule_df, rooms, courses)

            # Export results
            schedule_df.to_excel('./schedule_results.xlsx', index=False)

            print("Schedule optimization completed successfully")
            print("\nAnalysis Results:")
            print(analysis)
        else:
            print("No viable solution found")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
