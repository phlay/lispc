(set L '(2 3 5 7 11 13))
(set sqL '(4 9 25 49 121 169))

(defun main ()
  (test (map (lambda (x) (* x x)) L) sqL))
