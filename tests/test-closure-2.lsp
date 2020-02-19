(defun foo (a b c)
  ( (lambda (d)
      (lambda (x y z)
	(list y d x a b z))) c ))

(set bar (foo 1 2 3))

(defun main ()
  (test (bar 11 22 33) '(22 3 11 1 2 33)))
