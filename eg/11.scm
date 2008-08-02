(define (main)
  (with-purse-module complaining-keeper
   (lambda (purse? make-purse! purse-balance! purse-transfer!)
     ; XXX ok, we really need a new naming convention!
     ;  among other things

     (let ((make-purse     (make-asker make-purse!     'make-purse))
           (purse-balance  (make-asker purse-balance!  'get-balance))
           (purse-transfer (make-asker purse-transfer! 'transfer)))
       (let ((alice (make-purse 42))
             (bob   (make-purse 0)))
         (print (purse-transfer (list bob alice 10)))
         (print (purse-balance alice))
         (print (purse-balance bob))
         (print (purse-transfer (list bob alice 100))))))))

(define (with-purse-module keeper f)
  (with-new-sealer 'purse
   (lambda (seal unseal purse?)
     (local

      ((define (purse-maker-server ? !)
         (let loop ()
           (let ((m (?)))
             (let ((tag (car m)) (arg (cadr m)) (k (caddr m)))
               (case tag
                 ((make-purse)
                  (cond ((not (number? arg)) (k 'bad-type))
                        ((< arg 0) (k 'negative-amount))
                        (else 
                         (k (seal (sprout-spawn keeper
                                                (make-purse-server arg))))))
                  (loop)))))))

       (define (make-purse-server initial-amount)
         (lambda (? !)
           (let loop ((balance initial-amount))
             (let ((m (?)))
               (let ((tag (car m)) (arg (cadr m)) (k (caddr m)))
                 (case tag
                   ((get-balance)
                    (k balance)
                    (loop balance))
                   ((add)
                    (let ((new-balance (+ balance arg)))
                      (cond ((< new-balance 0)
                             (k 'insufficient-funds)
                             (loop balance))
                            (else
                             (k 'ok)
                             (loop new-balance)))))))))))
     
       (define (purse-balance-server ? !)
         (let loop ()
           (let ((m (?)))
             (let ((tag (car m)) (arg (cadr m)) (k (caddr m)))
               (case tag
                 ((get-balance)
                  ((unseal arg) (list tag #f k))
                  (loop)))))))

       (define (purse-transfer-server ? !)
         (let loop ()
           (let ((m (?)))
             (let ((tag (car m)) (arg (cadr m)) (k (caddr m)))
               (case tag
                 ((transfer)
                  (let ((to-purse   (unseal (car arg)))
                        (from-purse (unseal (cadr arg)))
                        (amount     (caddr arg)))
                    (if (< amount 0) 
                        (k 'negative-amount)
                        (let ((plaint (ask from-purse 'add (- amount))))
                          (if (not (equal? 'ok plaint))
                              (k plaint)
                              (to-purse (list 'add amount k))))))
                  (loop))))))))

      (f purse?
         (sprout-spawn keeper purse-maker-server)
         (sprout-spawn keeper purse-balance-server)
         (sprout-spawn keeper purse-transfer-server))))))

(define (sprout-spawn keeper fn)
  (with-new-channel
   (lambda (initial-? initial-!)
     (spawn keeper (lambda ()
                     (with-new-channel
                      (lambda (? !)
                        (initial-! !)
                        (fn ? !)))))
     (initial-?))))

(define (with-new-channel f)
  (let ((pair (sprout)))
    (f (car pair) (cadr pair))))

(define (with-new-sealer name f)
  (let ((triple (make-sealer name)))
    (f (car triple) (cadr triple) (caddr triple))))

(define (make-asker server! tag)
  (lambda (message)
    (ask server! tag message)))

(define (ask server! tag message)
  (with-new-channel
   (lambda (? !)
     (server! (list tag message !))
     (?))))