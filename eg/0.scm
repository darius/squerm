(define (main) 
  (write (spawn (lambda (! ?) 
		  (whee (list 'a)))))
  (newline)
  (write 'yo)
  (newline))

(define (whee x)
  (write (cons x (cons 'b '())))
  (newline))
