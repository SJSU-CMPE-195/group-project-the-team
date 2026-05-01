import numpy as np
import collections

class HandGeometry:
    def __init__(self):
        # Motion Buffers for Dynamic Signs (Z, J)
        self.index_history = collections.deque(maxlen=20)
        self.pinky_history = collections.deque(maxlen=20)

    def _dist(self, p1, p2):
        return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)

    def _is_highest(self, lm, target_idx, other_indices):
        target_y = lm[target_idx].y
        for idx in other_indices:
            if lm[idx].y < target_y:
                return False
        return True
        
    def _is_lowest(self, lm, target_idx, other_indices):
        """Returns True if the target has the LARGEST Y value (lowest on screen)"""
        target_y = lm[target_idx].y
        for idx in other_indices:
            if lm[idx].y > target_y:
                return False
        return True

    def _has_significant_motion(self, history, threshold=0.08):
        """Checks if a point has moved significantly in the last N frames"""
        if len(history) < 15:
            return False
        xs = [p[0] for p in history]
        ys = [p[1] for p in history]
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        return width > threshold or height > threshold

    def get_spatial_features(self, lm):
        wrist = lm[0]
        
        # Update Motion History
        self.index_history.append((lm[8].x, lm[8].y))
        self.pinky_history.append((lm[20].x, lm[20].y))
        
        # 1. Extension
        ext = []
        for tip, base in [(8,5), (12,9), (16,13), (20,17)]:
            ext.append(self._dist(lm[tip], wrist) > self._dist(lm[base], wrist) * 1.3)
            
        # 2. Elevation
        up = []
        for tip, pip in [(8,6), (12,10), (16,14), (20,18)]:
            up.append(lm[tip].y < lm[pip].y)
            
        # 3. Touching Distances
        d_it = self._dist(lm[4], lm[8])  
        d_mt = self._dist(lm[4], lm[12]) 
        d_rt = self._dist(lm[4], lm[16]) 
        d_im = self._dist(lm[8], lm[12])
        d_mr = self._dist(lm[12], lm[16])
        
        # 4. Highest/Lowest Points
        highest_pt_idx = 0
        min_y = 1.0
        for i in range(21):
            if lm[i].y < min_y:
                min_y = lm[i].y
                highest_pt_idx = i
                
        thumb_is_lowest = self._is_lowest(lm, 4, [8, 12, 16, 20])

        # 5. Complex Poses
        index_is_horizontal = abs(lm[8].x - lm[5].x) > abs(lm[8].y - lm[5].y)
        index_pointing_down = (lm[8].y > lm[5].y) and not index_is_horizontal
        thumb_pointing_down = (lm[4].y > lm[2].y)
        
        crossed_im = lm[8].x > lm[12].x
        thumb_out = self._dist(lm[4], lm[5]) > 0.08
        
        # 6. User's Hook Logic (X): Tip is bent lower than DIP(7), but higher than Knuckle(5)
        hooked_index = (lm[8].y > lm[7].y) and (lm[8].y < lm[5].y)

        # 7. User's K Logic: Thumb tip (4) touches Middle PIP (10)
        thumb_on_middle = self._dist(lm[4], lm[10]) < 0.06
        
        # 8. User's E Logic: Tips are curled UNDER PIPs
        tips_curled_tight = (lm[8].y > lm[6].y) and (lm[12].y > lm[10].y)

        return {
            "ext": ext, "up": up, 
            "d_it": d_it, "d_mt": d_mt, "d_rt": d_rt,
            "d_im": d_im, "d_mr": d_mr,
            "crossed": crossed_im, "thumb_out": thumb_out, 
            "highest": highest_pt_idx, "hooked_index": hooked_index,
            "horizontal_index": index_is_horizontal,
            "thumb_is_lowest": thumb_is_lowest,
            "thumb_on_middle": thumb_on_middle,
            "tips_curled_tight": tips_curled_tight,
            "index_down": index_pointing_down,
            "thumb_down": thumb_pointing_down
        }

    def classify_letter(self, lm):
        f = self.get_spatial_features(lm)
        ext = f["ext"]
        up = f["up"]
        highest = f["highest"]
        
        # --- DYNAMIC SIGNS (Z, J) ---
        # Z: Hand is in 'D' shape, but Index finger is moving significantly
        is_d_shape = ext[0] and not any(ext[1:]) and f["d_mt"] < 0.05
        if is_d_shape and self._has_significant_motion(self.index_history, threshold=0.10):
            return "Z"
            
        # J: Hand is in 'I' shape, but Pinky finger is moving significantly
        is_i_shape = ext[3] and not any(ext[:3]) and not f["thumb_out"]
        if is_i_shape and self._has_significant_motion(self.pinky_history, threshold=0.08):
            return "J"
        
        # --- STATIC GEOMETRIC ENGINE ---
        
        if is_d_shape: return "D"
        if is_i_shape: return "I"
        
        # A: Thumb tip (4) is the highest point
        if highest == 4 and not any(ext): return "A"
        
        # N: Thumb tucked under Middle finger pushes the Middle PIP/Base (9 or 10) to the top
        if highest in [9, 10] and not any(ext): return "N"
        
        # M: Thumb tucked under Ring finger pushes the Ring PIP/Base (13 or 14) to the top
        if highest in [13, 14] and not any(ext): return "M"
        
        # T: Thumb tucked between Index and Middle.
        if highest in [5, 6] and not any(ext) and f["d_it"] < 0.05: return "T"
        
        # C: Thumb is the absolute LOWEST point, and fingers are curved above it
        if f["thumb_is_lowest"] and not any(ext) and f["d_it"] > 0.08: return "C"
        
        # E: All finger tips are tightly curled UNDER their knuckles, thumb tucked
        if f["tips_curled_tight"] and not any(ext) and f["d_it"] < 0.05: return "E"
        
        # K: Index and Middle UP, separated (V-shape). Thumb is between them (touching Middle PIP).
        if ext[0] and ext[1] and not any(ext[2:]) and f["d_im"] > 0.04 and f["thumb_on_middle"]: return "K"
        
        # Y: Thumb OUT and Pinky UP. Others explicitly down.
        if f["thumb_out"] and ext[3] and not any(ext[:3]): return "Y"
        
        # X: Index hooked (tip lower than DIP, but higher than base).
        if f["hooked_index"] and not any(ext[1:]): return "X"
        
        # P: Index and Middle pointing DOWN.
        if ext[0] and ext[1] and f["index_down"] and not any(ext[2:]) and f["d_im"] > 0.03: return "P"
        
        # Q: Index and Thumb pointing DOWN, other fingers curled.
        if f["index_down"] and f["thumb_down"] and not any(ext[1:]): return "Q"
        
        # G: Index is horizontal.
        if f["horizontal_index"] and not any(ext[1:]) and not up[0] and not f["index_down"]: return "G"
        
        # B: All fingers extended and touching
        if all(ext) and f["d_im"] < 0.04 and f["d_mr"] < 0.04: return "B"
        
        # F: Index and Thumb touching (OK sign). Middle, Ring, Pinky extended UP.
        if f["d_it"] < 0.035 and all(ext[1:]): return "F"
        
        # H: Index and Middle extended horizontally (NOT up).
        if ext[0] and ext[1] and f["horizontal_index"] and not any(ext[2:]): return "H"
        
        # L: Index extended UP, Thumb extended OUT.
        if ext[0] and f["thumb_out"] and not any(ext[1:]) and not f["horizontal_index"]: return "L"
        
        # O: All tips touching the thumb.
        if not any(ext) and f["d_it"] < 0.05 and f["d_mt"] < 0.05 and f["d_rt"] < 0.05: return "O"
        
        # R: Index and Middle UP and crossed.
        if ext[0] and ext[1] and not any(ext[2:]) and f["crossed"]: return "R"
        
        # S: Fist, thumb crossed over the front of the fingers.
        if not any(ext) and highest not in [4, 9, 10, 13, 14] and f["d_it"] > 0.04 and f["d_mt"] > 0.04: return "S"
        
        # U: Index and Middle UP and touching.
        if ext[0] and ext[1] and not any(ext[2:]) and f["d_im"] < 0.045 and not f["crossed"] and not f["thumb_on_middle"]: return "U"
        
        # V: Index and Middle UP and separated (Peace sign).
        if ext[0] and ext[1] and not any(ext[2:]) and f["d_im"] >= 0.045 and not f["crossed"] and not f["thumb_on_middle"]: return "V"
        
        # W: Index, Middle, Ring UP.
        if all(ext[:3]) and not ext[3]: return "W"
        
        return None
