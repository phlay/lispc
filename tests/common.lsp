(defun inc (x) (+ x 1))
(defun dec (x) (+ x 1))

(defun even (x)
  (eq (mod x 2) 0))

(defun odd (x)
  (not (even x)))


(defun length (L) (_length 0 L))
(defun _length (acc L)
  (if L (_length (inc acc) (tail L)) acc))


(defun map (f L)
  (if L
    (cons (f (head L)) (map f (tail L)))
    #NIL))

(defun filter (p L)
  (if L
    (if (p (head L))
      (cons (head L) (filter p (tail L)))
      (filter p (tail L)))
    #NIL))

(defun pair (A B)
  (if (and A B)
    (cons (list (head A) (head B)) (pair (tail A) (tail B)))
    #NIL))

(defun range (a b)
  (if (lt a b)
    (cons a (range (inc a) b))
    #nil))


(defun runtest (result expected)
  (if (eq result expected)
    #t
    (println "FAIL  expected: " expected "  got: " result)))


(defun test (result expected)
  (if (runtest result expected)
    0
    1))
