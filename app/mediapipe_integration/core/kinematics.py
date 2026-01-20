"""
Kinematics Module for MEMOTION.

Contains functions for calculating joint angles, motion analysis, etc.
"""

import math
from typing import List, Tuple, Optional
import numpy as np

from .data_types import Point3D, JointType, JOINT_DEFINITIONS, PoseLandmarkIndex


def calculate_joint_angle(joint1: Point3D, joint2: Point3D, joint3: Point3D) -> float:
    """
    Calculate angle at joint2 formed by joint1-joint2-joint3.

    Args:
        joint1: First joint point
        joint2: Middle joint point (angle vertex)
        joint3: Third joint point

    Returns:
        Angle in degrees
    """
    # Convert to numpy arrays
    p1 = np.array([joint1.x, joint1.y, joint1.z])
    p2 = np.array([joint2.x, joint2.y, joint2.z])
    p3 = np.array([joint3.x, joint3.y, joint3.z])

    # Vectors
    v1 = p1 - p2
    v2 = p3 - p2

    # Cosine of angle
    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    cos_angle = np.clip(cos_angle, -1, 1)  # Handle floating point errors

    angle_rad = np.arccos(cos_angle)
    angle_deg = np.degrees(angle_rad)

    return angle_deg


def calculate_angle_from_landmarks(landmarks: List[Point3D], joint_type: JointType) -> float:
    """
    Calculate joint angle from landmarks.

    Args:
        landmarks: List of 3D points
        joint_type: Type of joint to calculate

    Returns:
        Angle in degrees
    """
    if joint_type not in JOINT_DEFINITIONS:
        return 0.0

    joint_indices = JOINT_DEFINITIONS[joint_type]['joints']

    if len(landmarks) <= max(joint_indices):
        return 0.0

    joint1 = landmarks[joint_indices[0]]
    joint2 = landmarks[joint_indices[1]]
    joint3 = landmarks[joint_indices[2]]

    return calculate_joint_angle(joint1, joint2, joint3)


def compute_single_joint_dtw(user_angles: List[float], reference_angles: List[float]) -> float:
    """
    Compute DTW distance for single joint motion sync.

    Args:
        user_angles: User's joint angles over time
        reference_angles: Reference joint angles

    Returns:
        DTW distance (lower is better sync)
    """
    n = len(user_angles)
    m = len(reference_angles)

    if n == 0 or m == 0:
        return float('inf')

    # Initialize DTW matrix
    dtw = np.full((n+1, m+1), float('inf'))
    dtw[0, 0] = 0

    for i in range(1, n+1):
        for j in range(1, m+1):
            cost = abs(user_angles[i-1] - reference_angles[j-1])
            dtw[i, j] = cost + min(
                dtw[i-1, j],    # insertion
                dtw[i, j-1],    # deletion
                dtw[i-1, j-1]   # match
            )

    return dtw[n, m]


def normalize_skeleton(landmarks: List[Point3D]) -> Tuple[List[Point3D], Point3D, float]:
    """
    Normalize skeleton by centering and scaling.

    Args:
        landmarks: Raw landmarks

    Returns:
        Tuple of (normalized_landmarks, center, scale)
    """
    if not landmarks:
        return [], Point3D(0, 0, 0), 1.0

    # Calculate center
    xs = [p.x for p in landmarks]
    ys = [p.y for p in landmarks]
    zs = [p.z for p in landmarks]

    center = Point3D(
        x=sum(xs) / len(xs),
        y=sum(ys) / len(ys),
        z=sum(zs) / len(zs)
    )

    # Calculate scale (distance between shoulders)
    left_shoulder = landmarks[PoseLandmarkIndex.LEFT_SHOULDER]
    right_shoulder = landmarks[PoseLandmarkIndex.RIGHT_SHOULDER]

    shoulder_distance = math.sqrt(
        (left_shoulder.x - right_shoulder.x)**2 +
        (left_shoulder.y - right_shoulder.y)**2 +
        (left_shoulder.z - right_shoulder.z)**2
    )

    scale = shoulder_distance if shoulder_distance > 0 else 1.0

    # Normalize
    normalized = []
    for point in landmarks:
        normalized.append(Point3D(
            x=(point.x - center.x) / scale,
            y=(point.y - center.y) / scale,
            z=(point.z - center.z) / scale
        ))

    return normalized, center, scale


def procrustes_analysis(source: List[Point3D], target: List[Point3D]) -> Tuple[np.ndarray, np.ndarray, float, float]:
    """
    Perform Procrustes analysis to align source to target.

    Args:
        source: Source landmarks
        target: Target landmarks

    Returns:
        Tuple of (rotation_matrix, translation, scale, disparity)
    """
    if len(source) != len(target) or len(source) < 3:
        return np.eye(3), np.zeros(3), 1.0, 0.0

    # Convert to numpy arrays
    source_array = np.array([[p.x, p.y, p.z] for p in source])
    target_array = np.array([[p.x, p.y, p.z] for p in target])

    # Center the points
    source_centroid = np.mean(source_array, axis=0)
    target_centroid = np.mean(target_array, axis=0)

    source_centered = source_array - source_centroid
    target_centered = target_array - target_centroid

    # Scale
    source_scale = np.sqrt(np.sum(source_centered**2))
    target_scale = np.sqrt(np.sum(target_centered**2))

    if source_scale > 0:
        source_centered /= source_scale
    if target_scale > 0:
        target_centered /= target_scale

    # Rotation using SVD
    H = np.dot(source_centered.T, target_centered)
    U, s, Vt = np.linalg.svd(H)
    R = np.dot(Vt.T, U.T)

    # Ensure right-handed coordinate system
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = np.dot(Vt.T, U.T)

    # Scale
    scale = target_scale / source_scale if source_scale > 0 else 1.0

    # Translation
    translation = target_centroid - scale * np.dot(R, source_centroid)

    # Disparity
    aligned_source = scale * np.dot(source_array, R) + translation
    disparity = np.mean(np.sum((aligned_source - target_array)**2, axis=1))

    return R, translation, scale, disparity