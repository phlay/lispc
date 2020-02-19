(defun F (a)
  (lambda (x) (+ x a)))

(set foo (F 19))

(defun main ()
  (test (foo 23) 42))

