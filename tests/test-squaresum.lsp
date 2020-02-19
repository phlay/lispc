(defun sq (x)
  (* x x))

(defun sum (L) (_sum 0 L))

(defun _sum (acc L)
  (if L
    (_sum (+ acc (head L)) (tail L))
    acc))

(set N 100)


(defun main ()
  (test (sum (filter odd (range 1 N)))
	(sq (/ N 2))))
